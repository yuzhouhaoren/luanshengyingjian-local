from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Optional

import torch
import torch.nn.functional as F


TensorDict = Dict[str, torch.Tensor]


@dataclass(frozen=True)
# 损失函数配置：主损失、辅助损失与稳定化参数
class LossConfig:
    main_weight: float = 1.0
    preference_aux_weight: float = 0.2
    intent_aux_weight: float = 0.2
    l2_weight: float = 0.0
    label_smoothing: float = 0.0
    positive_class_weight: float = 1.0
    clamp_logits: float = 30.0


# 对二分类标签做平滑，缓解过拟合和过度自信
def _smooth_labels(labels: torch.Tensor, smoothing: float) -> torch.Tensor:
    s = float(smoothing)
    s = max(0.0, min(0.2, s))
    if s <= 1e-8:
        return labels
    return labels * (1.0 - s) + 0.5 * s


# 构建正类权重张量，用于处理类别不平衡
def _build_pos_weight(labels: torch.Tensor, positive_class_weight: float) -> torch.Tensor:
    w = max(0.1, float(positive_class_weight))
    return torch.tensor(w, dtype=labels.dtype, device=labels.device)


# 计算模型 L2 正则项（仅统计矩阵参数）
def _l2_regularization(model: Optional[torch.nn.Module]) -> torch.Tensor:
    if model is None:
        return torch.tensor(0.0)

    # 只对矩阵参数做 L2，避免把 bias 和标量参数放大得太明显
    l2 = None
    for p in model.parameters():
        if not p.requires_grad:
            continue
        if p.ndim < 2:
            continue
        term = torch.sum(p * p)
        l2 = term if l2 is None else (l2 + term)

    if l2 is None:
        return torch.tensor(0.0)
    return l2


def compute_train_loss(
    outputs: TensorDict,
    batch: TensorDict,
    config: LossConfig,
    model: Optional[torch.nn.Module] = None,
) -> TensorDict:
    # 计算训练阶段总损失，并返回便于日志统计的指标
    if "label" not in batch:
        raise KeyError("batch must contain key: label")
    if "final_logit" not in outputs:
        raise KeyError("outputs must contain key: final_logit")
    if "preference_logit" not in outputs:
        raise KeyError("outputs must contain key: preference_logit")
    if "intent_logit" not in outputs:
        raise KeyError("outputs must contain key: intent_logit")

    labels = batch["label"].float().view(-1)
    labels = _smooth_labels(labels, config.label_smoothing)

    pos_weight = _build_pos_weight(labels, config.positive_class_weight)
    clamp_v = max(1.0, float(config.clamp_logits))

    final_logit = torch.clamp(outputs["final_logit"].view(-1), -clamp_v, clamp_v)
    preference_logit = torch.clamp(outputs["preference_logit"].view(-1), -clamp_v, clamp_v)
    intent_logit = torch.clamp(outputs["intent_logit"].view(-1), -clamp_v, clamp_v)

    main_loss = F.binary_cross_entropy_with_logits(
        final_logit,
        labels,
        pos_weight=pos_weight,
    )
    preference_loss = F.binary_cross_entropy_with_logits(
        preference_logit,
        labels,
        pos_weight=pos_weight,
    )
    intent_loss = F.binary_cross_entropy_with_logits(
        intent_logit,
        labels,
        pos_weight=pos_weight,
    )

    l2_term = _l2_regularization(model)

    total_loss = (
        float(config.main_weight) * main_loss
        + float(config.preference_aux_weight) * preference_loss
        + float(config.intent_aux_weight) * intent_loss
        + float(config.l2_weight) * l2_term
    )

    with torch.no_grad():
        probs = torch.sigmoid(final_logit)
        preds = (probs >= 0.5).to(labels.dtype)
        hard_labels = (labels >= 0.5).to(labels.dtype)

        accuracy = torch.mean((preds == hard_labels).to(labels.dtype))
        mean_prob = torch.mean(probs)
        pos_rate = torch.mean(hard_labels)

    return {
        "total_loss": total_loss,
        "main_loss": main_loss.detach(),
        "preference_loss": preference_loss.detach(),
        "intent_loss": intent_loss.detach(),
        "l2_loss": l2_term.detach() if isinstance(l2_term, torch.Tensor) else torch.tensor(0.0),
        "accuracy": accuracy.detach(),
        "mean_prob": mean_prob.detach(),
        "pos_rate": pos_rate.detach(),
    }


def compute_eval_loss(
    outputs: TensorDict,
    batch: TensorDict,
    config: LossConfig,
) -> TensorDict:
    # 计算验证阶段损失，默认关闭标签平滑和 L2 正则
    # 验证阶段默认不做标签平滑和 L2 正则
    eval_cfg = replace(config, l2_weight=0.0, label_smoothing=0.0)
    return compute_train_loss(outputs=outputs, batch=batch, config=eval_cfg, model=None)
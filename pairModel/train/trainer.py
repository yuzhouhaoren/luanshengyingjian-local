from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import torch
from torch.utils.data import DataLoader

from .dataset import PairDataset, collate_pair_batch
from .losses import LossConfig, compute_eval_loss, compute_train_loss
from .model_net import DualTowerTrainConfig, DualTowerTrainModel


MetricDict = Dict[str, float]
Sample = Dict[str, Any]


@dataclass(frozen=True)
# 训练流程配置
class TrainerConfig:
    batch_size: int = 64
    num_epochs: int = 20
    learning_rate: float = 1e-3
    weight_decay: float = 1e-5
    grad_clip_norm: float = 1.0
    num_workers: int = 0
    early_stop_patience: int = 4
    device: str = "cuda"
    seed: int = 42
    log_every_steps: int = 20


# 根据配置优先选择可用的训练设备
def _pick_device(device_hint: str) -> torch.device:
    hint = str(device_hint or "").strip().lower()
    if hint.startswith("cuda") and torch.cuda.is_available():
        return torch.device("cuda")
    if hint == "mps" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


# 将张量或数值统一转为 Python float
def _to_float(x: Any) -> float:
    if isinstance(x, torch.Tensor):
        return float(x.detach().cpu().item())
    return float(x)


# 对多步指标做平均，便于输出 epoch 级统计
def _avg_metrics(metric_list: Sequence[Dict[str, Any]]) -> MetricDict:
    if not metric_list:
        return {
            "total_loss": 0.0,
            "main_loss": 0.0,
            "preference_loss": 0.0,
            "intent_loss": 0.0,
            "l2_loss": 0.0,
            "accuracy": 0.0,
            "mean_prob": 0.0,
            "pos_rate": 0.0,
        }

    keys = list(metric_list[0].keys())
    out: MetricDict = {}
    for k in keys:
        vals = [_to_float(m[k]) for m in metric_list if k in m]
        out[k] = float(np.mean(vals)) if vals else 0.0
    return out


# 将一个 batch 中的张量迁移到指定设备
def _batch_to_device(batch: Dict[str, Any], device: torch.device) -> Dict[str, Any]:
    return {
        "seeker_profile": batch["seeker_profile"].to(device),
        "seeker_intent": batch["seeker_intent"].to(device),
        "candidate_profile": batch["candidate_profile"].to(device),
        "candidate_intent": batch["candidate_intent"].to(device),
        "label": batch["label"].to(device),
        "meta": batch["meta"],
    }


# 构造 DataLoader，统一 batch 与 collate 配置
def _make_loader(
    dataset: PairDataset,
    batch_size: int,
    shuffle: bool,
    num_workers: int,
) -> DataLoader:
    return DataLoader(
        dataset,
        batch_size=max(1, int(batch_size)),
        shuffle=bool(shuffle),
        num_workers=max(0, int(num_workers)),
        collate_fn=collate_pair_batch,
        drop_last=False,
    )


# 执行一个训练轮次，返回该轮平均指标
def train_one_epoch(
    model: DualTowerTrainModel,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    loss_config: LossConfig,
    device: torch.device,
    grad_clip_norm: float = 1.0,
    log_every_steps: int = 0,
) -> MetricDict:
    model.train()
    all_metrics: List[Dict[str, Any]] = []

    for step_idx, batch in enumerate(loader, start=1):
        # 将 batch 放到同一设备上进行前向和反向计算
        batch = _batch_to_device(batch, device)

        outputs = model(
            seeker_profile=batch["seeker_profile"],
            seeker_intent=batch["seeker_intent"],
            candidate_profile=batch["candidate_profile"],
            candidate_intent=batch["candidate_intent"],
        )
        metric = compute_train_loss(outputs=outputs, batch=batch, config=loss_config, model=model)

        loss = metric["total_loss"]
        optimizer.zero_grad(set_to_none=True)
        loss.backward()

        # 梯度裁剪，抑制梯度爆炸
        if grad_clip_norm and float(grad_clip_norm) > 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=float(grad_clip_norm))

        optimizer.step()

        all_metrics.append(metric)

        if log_every_steps and step_idx % int(log_every_steps) == 0:
            avg_now = _avg_metrics(all_metrics[-int(log_every_steps) :])
            print(
                f"[train] step={step_idx} "
                f"loss={avg_now['total_loss']:.4f} "
                f"acc={avg_now['accuracy']:.4f}"
            )

    return _avg_metrics(all_metrics)


@torch.no_grad()
# 执行一个验证轮次，返回该轮平均指标
def evaluate_one_epoch(
    model: DualTowerTrainModel,
    loader: DataLoader,
    loss_config: LossConfig,
    device: torch.device,
) -> MetricDict:
    model.eval()
    all_metrics: List[Dict[str, Any]] = []

    for batch in loader:
        batch = _batch_to_device(batch, device)

        outputs = model(
            seeker_profile=batch["seeker_profile"],
            seeker_intent=batch["seeker_intent"],
            candidate_profile=batch["candidate_profile"],
            candidate_intent=batch["candidate_intent"],
        )
        metric = compute_eval_loss(outputs=outputs, batch=batch, config=loss_config)
        all_metrics.append(metric)

    return _avg_metrics(all_metrics)


# 训练入口：完成数据集、模型、优化器初始化并执行完整训练流程
def fit_dual_tower(
    train_samples: Sequence[Sample],
    val_samples: Sequence[Sample],
    model_config: DualTowerTrainConfig,
    loss_config: LossConfig,
    trainer_config: TrainerConfig,
) -> Dict[str, Any]:
    if len(train_samples) == 0:
        raise ValueError("train_samples is empty")
    if len(val_samples) == 0:
        raise ValueError("val_samples is empty")

    # 固定随机种子，尽量保证训练可复现
    torch.manual_seed(int(trainer_config.seed))
    np.random.seed(int(trainer_config.seed))

    train_dataset = PairDataset(
        samples=train_samples,
        intent_dim=model_config.intent_input_dim,
        profile_dim=model_config.profile_input_dim,
    )
    val_dataset = PairDataset(
        samples=val_samples,
        intent_dim=model_config.intent_input_dim,
        profile_dim=model_config.profile_input_dim,
    )

    train_loader = _make_loader(
        dataset=train_dataset,
        batch_size=trainer_config.batch_size,
        shuffle=True,
        num_workers=trainer_config.num_workers,
    )
    val_loader = _make_loader(
        dataset=val_dataset,
        batch_size=trainer_config.batch_size,
        shuffle=False,
        num_workers=trainer_config.num_workers,
    )

    device = _pick_device(trainer_config.device)
    model = DualTowerTrainModel(config=model_config).to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(trainer_config.learning_rate),
        weight_decay=float(trainer_config.weight_decay),
    )

    best_state: Optional[Dict[str, torch.Tensor]] = None
    best_epoch = -1
    best_val_loss = float("inf")
    no_improve = 0

    history: List[Dict[str, Any]] = []

    for epoch in range(1, int(trainer_config.num_epochs) + 1):
        train_metrics = train_one_epoch(
            model=model,
            loader=train_loader,
            optimizer=optimizer,
            loss_config=loss_config,
            device=device,
            grad_clip_norm=trainer_config.grad_clip_norm,
            log_every_steps=trainer_config.log_every_steps,
        )
        val_metrics = evaluate_one_epoch(
            model=model,
            loader=val_loader,
            loss_config=loss_config,
            device=device,
        )

        row = {
            "epoch": epoch,
            "train": train_metrics,
            "val": val_metrics,
        }
        history.append(row)

        print(
            f"[epoch {epoch}] "
            f"train_loss={train_metrics['total_loss']:.4f} "
            f"train_acc={train_metrics['accuracy']:.4f} "
            f"val_loss={val_metrics['total_loss']:.4f} "
            f"val_acc={val_metrics['accuracy']:.4f}"
        )

        # 记录最优验证损失，并缓存最优参数
        cur_val = float(val_metrics["total_loss"])
        if cur_val < best_val_loss:
            best_val_loss = cur_val
            best_epoch = epoch
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            no_improve = 0
        else:
            no_improve += 1

        # 达到早停阈值后提前结束训练
        if no_improve >= int(trainer_config.early_stop_patience):
            print(f"[early-stop] epoch={epoch}, best_epoch={best_epoch}, best_val_loss={best_val_loss:.4f}")
            break

    # 恢复最优 epoch 的模型参数
    if best_state is not None:
        model.load_state_dict(best_state)

    result = {
        "model": model,
        "device": str(device),
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "history": history,
        "intent_dim": model_config.intent_input_dim,
        "profile_dim": model_config.profile_input_dim,
    }
    return result
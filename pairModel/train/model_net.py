from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass(frozen=True)
# 双塔训练模型配置
class DualTowerTrainConfig:
    intent_input_dim: int
    profile_input_dim: int
    tower_hidden_dim: int = 128
    tower_output_dim: int = 64
    dropout: float = 0.1
    use_profile: bool = True


# 两层 MLP 投影器，用于把输入特征映射到统一嵌入空间
class MLPProjector(nn.Module):
    # 初始化投影网络结构
    def __init__(self, in_dim: int, hidden_dim: int, out_dim: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, out_dim),
        )

    # 前向投影计算
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class DualTowerTrainModel(nn.Module):
    # 训练版双塔模型：
    # seeker 侧：意向塔（主塔）+ 画像塔
    # candidate 侧：意向塔 + 画像塔
    # 输出：preference_logit, intent_logit, final_logit

    # 根据配置构建双塔与融合参数
    def __init__(self, config: DualTowerTrainConfig) -> None:
        super().__init__()
        self.config = config

        if config.intent_input_dim <= 0:
            raise ValueError("intent_input_dim must be > 0")
        if config.profile_input_dim < 0:
            raise ValueError("profile_input_dim must be >= 0")
        if config.tower_output_dim <= 0:
            raise ValueError("tower_output_dim must be > 0")

        # 意向塔：用于 seeker_intent / candidate_intent
        self.intent_tower = MLPProjector(
            in_dim=config.intent_input_dim,
            hidden_dim=config.tower_hidden_dim,
            out_dim=config.tower_output_dim,
            dropout=config.dropout,
        )

        # 画像塔：用于 seeker_profile / candidate_profile
        if config.use_profile and config.profile_input_dim > 0:
            self.profile_tower = MLPProjector(
                in_dim=config.profile_input_dim,
                hidden_dim=config.tower_hidden_dim,
                out_dim=config.tower_output_dim,
                dropout=config.dropout,
            )
        else:
            self.profile_tower = None

        # 可学习融合权重（训练后可导出）
        self.preference_weight = nn.Parameter(torch.tensor(0.6, dtype=torch.float32))
        self.intent_weight = nn.Parameter(torch.tensor(0.4, dtype=torch.float32))

        # 全局缩放，控制 logit 幅度
        self.logit_scale = nn.Parameter(torch.tensor(8.0, dtype=torch.float32))

    @staticmethod
    # 计算两组向量的余弦相似度
    def _cosine(a: torch.Tensor, b: torch.Tensor, eps: float = 1e-8) -> torch.Tensor:
        a = F.normalize(a, dim=-1, eps=eps)
        b = F.normalize(b, dim=-1, eps=eps)
        return torch.sum(a * b, dim=-1)

    # 获取经过 softmax 归一化的融合权重
    def _get_fusion_weights(self) -> torch.Tensor:
        # softmax 保证权重非负且和为 1
        w = torch.stack([self.preference_weight, self.intent_weight], dim=0)
        return F.softmax(w, dim=0)

    # 执行前向计算并输出训练所需的分数与 logit
    def forward(
        self,
        seeker_profile: torch.Tensor,
        seeker_intent: torch.Tensor,
        candidate_profile: torch.Tensor,
        candidate_intent: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        # 意向编码
        seeker_intent_emb = self.intent_tower(seeker_intent)
        candidate_intent_emb = self.intent_tower(candidate_intent)

        # 意向一致度（辅助信号）
        intent_score = self._cosine(seeker_intent_emb, candidate_intent_emb)

        if self.profile_tower is not None:
            # 画像编码
            seeker_profile_emb = self.profile_tower(seeker_profile)
            candidate_profile_emb = self.profile_tower(candidate_profile)

            # 方向主信号：seeker 意向 vs candidate 画像
            preference_score = self._cosine(seeker_intent_emb, candidate_profile_emb)

            # 可选监控项：画像一致度（不直接入主融合，留给分析）
            profile_score = self._cosine(seeker_profile_emb, candidate_profile_emb)
        else:
            # 无画像塔时，主信号退化为意向信号
            preference_score = intent_score
            profile_score = torch.zeros_like(intent_score)

        fusion_w = self._get_fusion_weights()
        final_score = fusion_w[0] * preference_score + fusion_w[1] * intent_score

        scale = torch.clamp(self.logit_scale, min=1.0, max=30.0)
        preference_logit = scale * preference_score
        intent_logit = scale * intent_score
        final_logit = scale * final_score

        return {
            "preference_score": preference_score,
            "intent_score": intent_score,
            "profile_score": profile_score,
            "final_score": final_score,
            "preference_logit": preference_logit,
            "intent_logit": intent_logit,
            "final_logit": final_logit,
            "fusion_weight_preference": fusion_w[0].detach(),
            "fusion_weight_intent": fusion_w[1].detach(),
        }
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import numpy as np
import torch

from .artifacts import CachedArtifactLoader


# 将任意向量输入统一为一维 float32 ndarray
def _to_1d_float_vector(value: Any) -> np.ndarray:
    if value is None:
        return np.asarray([], dtype=np.float32)

    arr = np.asarray(value, dtype=np.float32)
    if arr.ndim == 0:
        arr = arr.reshape(1)
    elif arr.ndim > 1:
        arr = arr.reshape(-1)
    return arr


# 将向量裁剪或零填充到目标维度
def _pad_or_clip(vec: np.ndarray, target_dim: int) -> np.ndarray:
    if target_dim <= 0:
        return np.asarray([], dtype=np.float32)

    if vec.size == target_dim:
        return vec.astype(np.float32, copy=False)

    if vec.size > target_dim:
        return vec[:target_dim].astype(np.float32, copy=False)

    out = np.zeros(target_dim, dtype=np.float32)
    if vec.size > 0:
        out[: vec.size] = vec
    return out


# 将业务意向类型映射到模型目录子路径
def _intent_to_subdir(intent_type: str) -> str:
    text = str(intent_type or "").strip()
    if text in {"伴侣", "intent_伴侣"}:
        return "partner"
    return "friend"


# 推理封装：按需加载训练产物并执行打分
class TrainedDualTowerInferencer:
    # 初始化推理器并准备缓存加载器
    def __init__(self) -> None:
        self._loader = CachedArtifactLoader()

    # 执行一次双塔打分，返回 [-1, 1] 范围内分数
    def score(
        self,
        seeker_profile_vector: Any,
        seeker_intent_vector: Any,
        candidate_profile_vector: Any,
        candidate_intent_vector: Any,
        intent_type: str,
        artifacts_root: str | Path,
        map_location: str = "cpu",
        force_reload: bool = False,
    ) -> Optional[float]:
        subdir = _intent_to_subdir(intent_type)
        model_dir = Path(artifacts_root) / subdir

        if not model_dir.exists():
            return None

        try:
            model, model_cfg, _loss_cfg, _stats = self._loader.get(
                save_dir=model_dir,
                map_location=map_location,
                force_reload=force_reload,
            )
        except Exception:
            return None

        try:
            device = next(model.parameters()).device
        except StopIteration:
            device = torch.device("cpu")

        seeker_profile = torch.from_numpy(
            _pad_or_clip(_to_1d_float_vector(seeker_profile_vector), int(model_cfg.profile_input_dim))
        ).unsqueeze(0).to(device)
        seeker_intent = torch.from_numpy(
            _pad_or_clip(_to_1d_float_vector(seeker_intent_vector), int(model_cfg.intent_input_dim))
        ).unsqueeze(0).to(device)
        candidate_profile = torch.from_numpy(
            _pad_or_clip(_to_1d_float_vector(candidate_profile_vector), int(model_cfg.profile_input_dim))
        ).unsqueeze(0).to(device)
        candidate_intent = torch.from_numpy(
            _pad_or_clip(_to_1d_float_vector(candidate_intent_vector), int(model_cfg.intent_input_dim))
        ).unsqueeze(0).to(device)

        with torch.no_grad():
            outputs = model(
                seeker_profile=seeker_profile,
                seeker_intent=seeker_intent,
                candidate_profile=candidate_profile,
                candidate_intent=candidate_intent,
            )

        if "final_score" in outputs:
            raw = outputs["final_score"].view(-1)[0]
        elif "final_logit" in outputs:
            # 兼容兜底：若模型只返回 logit，则通过 tanh 映射到分数
            raw = torch.tanh(outputs["final_logit"].view(-1)[0])
        else:
            return None

        score = float(raw.detach().cpu().item())
        if not np.isfinite(score):
            return None
        return max(-1.0, min(1.0, score))


_INFERENCER = TrainedDualTowerInferencer()


# 对外提供的推理函数，供 matcher 直接调用
def trained_dual_tower_similarity(
    seeker_profile_vector: Any,
    seeker_intent_vector: Any,
    candidate_profile_vector: Any,
    candidate_intent_vector: Any,
    intent_type: str,
    artifacts_root: str | Path,
    map_location: str = "cpu",
    force_reload: bool = False,
) -> Optional[float]:
    return _INFERENCER.score(
        seeker_profile_vector=seeker_profile_vector,
        seeker_intent_vector=seeker_intent_vector,
        candidate_profile_vector=candidate_profile_vector,
        candidate_intent_vector=candidate_intent_vector,
        intent_type=intent_type,
        artifacts_root=artifacts_root,
        map_location=map_location,
        force_reload=force_reload,
    )

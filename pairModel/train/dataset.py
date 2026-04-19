from __future__ import annotations
from typing import Any, Dict, List, Optional, Sequence
import numpy as np
import torch
from torch.utils.data import Dataset

Sample = Dict[str, Any]


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


# 在样本中扫描指定字段，推断可用的最大向量维度
def _infer_dim(samples: Sequence[Sample], keys: Sequence[str], default: int) -> int:
    max_dim = 0
    for item in samples:
        for key in keys:
            size = int(_to_1d_float_vector(item.get(key)).size)
            if size > max_dim:
                max_dim = size

    if max_dim > 0:
        return max_dim
    return int(default)


# 将配对样本包装为可供 DataLoader 使用的数据集
class PairDataset(Dataset):
    # 把 build_labeled_pairs_from_db 产出的样本转换成可训练张量
    def __init__(
        self,
        samples: Sequence[Sample],
        intent_dim: Optional[int] = None,
        profile_dim: Optional[int] = None,
    ) -> None:
        # 清洗样本，过滤非字典、无 label 标签的残缺脏样本
        cleaned: List[Sample] = []
        for item in samples:
            if not isinstance(item, dict):
                continue
            if "label" not in item:
                continue
            cleaned.append(item)

        self.samples = cleaned
        # 自动推理向量维度
        inferred_intent_dim = _infer_dim(
            cleaned,
            keys=("seeker_intent_vector", "candidate_intent_vector"),
            default=1,
        )
        inferred_profile_dim = _infer_dim(
            cleaned,
            keys=("seeker_profile_vector", "candidate_profile_vector"),
            default=0,
        )

        self.intent_dim = int(intent_dim) if intent_dim is not None else inferred_intent_dim
        self.profile_dim = int(profile_dim) if profile_dim is not None else inferred_profile_dim

        if self.intent_dim <= 0:
            raise ValueError("intent_dim must be > 0")

        if self.profile_dim < 0:
            raise ValueError("profile_dim must be >= 0")

    # 返回样本数量
    def __len__(self) -> int:
        return len(self.samples)

    # 读取样本中的某个向量字段并编码为固定维度张量
    def _encode_vector(self, item: Sample, key: str, target_dim: int) -> torch.Tensor:
        raw = _to_1d_float_vector(item.get(key))
        vec = _pad_or_clip(raw, target_dim)
        return torch.from_numpy(vec)

    # 取单条样本并转换为训练所需的张量字典
    def __getitem__(self, index: int) -> Dict[str, Any]:
        item = self.samples[index]

        seeker_profile = self._encode_vector(item, "seeker_profile_vector", self.profile_dim)
        seeker_intent = self._encode_vector(item, "seeker_intent_vector", self.intent_dim)
        candidate_profile = self._encode_vector(item, "candidate_profile_vector", self.profile_dim)
        candidate_intent = self._encode_vector(item, "candidate_intent_vector", self.intent_dim)

        label = float(item.get("label", 0.0))
        label_tensor = torch.tensor(label, dtype=torch.float32)
        # 打包返回字典张量
        return {
            "seeker_profile": seeker_profile,
            "seeker_intent": seeker_intent,
            "candidate_profile": candidate_profile,
            "candidate_intent": candidate_intent,
            "label": label_tensor,
            "meta": {
                "seeker_id": str(item.get("seeker_id", "") or ""),
                "candidate_id": str(item.get("candidate_id", "") or ""),
                "intent_type": str(item.get("intent_type", "") or ""),
                "source": str(item.get("source", "") or ""),
            },
        }


# 将单样本列表拼接成 DataLoader 需要的批次结构
def collate_pair_batch(batch: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    if not batch:
        return {
            "seeker_profile": torch.empty((0, 0), dtype=torch.float32),
            "seeker_intent": torch.empty((0, 0), dtype=torch.float32),
            "candidate_profile": torch.empty((0, 0), dtype=torch.float32),
            "candidate_intent": torch.empty((0, 0), dtype=torch.float32),
            "label": torch.empty((0,), dtype=torch.float32),
            "meta": [],
        }

    return {
        "seeker_profile": torch.stack([x["seeker_profile"] for x in batch], dim=0),
        "seeker_intent": torch.stack([x["seeker_intent"] for x in batch], dim=0),
        "candidate_profile": torch.stack([x["candidate_profile"] for x in batch], dim=0),
        "candidate_intent": torch.stack([x["candidate_intent"] for x in batch], dim=0),
        "label": torch.stack([x["label"] for x in batch], dim=0),
        "meta": [x["meta"] for x in batch],
    }
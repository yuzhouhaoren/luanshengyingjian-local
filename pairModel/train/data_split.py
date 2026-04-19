from __future__ import annotations
from typing import Any, Dict, List, Sequence, Tuple
import numpy as np

Sample = Dict[str, Any]


# 判断样本标签是否为正类（> 0.5）
def _label_is_positive(item: Sample) -> bool:
    try:
        return float(item.get("label", 0.0)) > 0.5
    except (TypeError, ValueError):
        return False


# 使用可复现随机数生成器打乱样本顺序
def _shuffle(items: Sequence[Sample], rng: np.random.Generator) -> List[Sample]:
    if len(items) <= 1:
        return list(items)
    order = rng.permutation(len(items))
    return [items[int(i)] for i in order]


# 在保证训练/验证都非空的前提下，计算验证集大小
def _safe_val_count(total: int, ratio: float) -> int:
    # 保证两边都有样本：至少 1 条验证，至少 1 条训练
    if total <= 1:
        return 0
    raw = int(round(total * ratio))
    return min(total - 1, max(1, raw))


# 统计样本中的正负样本数量
def _count_pos_neg(items: Sequence[Sample]) -> Dict[str, int]:
    pos = 0
    for item in items:
        if _label_is_positive(item):
            pos += 1
    neg = len(items) - pos
    return {"pos": pos, "neg": neg}


# 判断样本中是否同时包含正负两类
def _has_both_labels(items: Sequence[Sample]) -> bool:
    c = _count_pos_neg(items)
    return c["pos"] > 0 and c["neg"] > 0


# 先按标签拆分，再分别抽取验证集，最后合并得到分层切分结果
def _split_stratified(
    samples: Sequence[Sample],
    val_ratio: float,
    rng: np.random.Generator,
) -> Tuple[List[Sample], List[Sample]]:
    positives = [x for x in samples if _label_is_positive(x)]
    negatives = [x for x in samples if not _label_is_positive(x)]

    positives = _shuffle(positives, rng)
    negatives = _shuffle(negatives, rng)

    #提取部分样本做验证集
    pos_val = _safe_val_count(len(positives), val_ratio) if len(positives) > 1 else 0
    neg_val = _safe_val_count(len(negatives), val_ratio) if len(negatives) > 1 else 0

    val = positives[:pos_val] + negatives[:neg_val]
    train = positives[pos_val:] + negatives[neg_val:]

    # 极小数据集兜底，避免出现空验证或空训练
    if not val and len(train) > 1:
        val.append(train.pop(0))
    if not train and len(val) > 1:
        train.append(val.pop(0))

    return _shuffle(train, rng), _shuffle(val, rng)


def split_train_val_pairs(
    samples: Sequence[Sample],
    val_ratio: float = 0.2,
    random_seed: int = 42,
    group_by_seeker: bool = True,
) -> Tuple[List[Sample], List[Sample], Dict[str, Any]]:
    # 将样本切成训练集和验证集
    # 默认按 seeker 分组切分，减少同一 seeker 泄露到 train/val 两边
    # 若分组切分后标签分布不健康，则自动回退到分层切分
    # 样本清洗：过滤无效结构和缺失标签的数据
    clean: List[Sample] = []
    for item in samples:
        if not isinstance(item, dict):
            continue
        if "label" not in item:
            continue
        clean.append(item)

    if len(clean) <= 1:
        stats = {
            "total": len(clean),
            "train": len(clean),
            "val": 0,
            "train_pos_neg": _count_pos_neg(clean),
            "val_pos_neg": {"pos": 0, "neg": 0},
            "strategy": "trivial",
        }
        return list(clean), [], stats

    ratio = float(val_ratio)
    ratio = min(0.5, max(0.05, ratio))
    rng = np.random.default_rng(int(random_seed))

    #按 seeker 分组切分，避免同一个用户同时出现在训练集和验证集
    if group_by_seeker:
        by_seeker: Dict[str, List[Sample]] = {}
        for item in clean:
            seeker_id = str(item.get("seeker_id", "") or "").strip()
            if not seeker_id:
                seeker_id = "__unknown__"
            by_seeker.setdefault(seeker_id, []).append(item)

        if len(by_seeker) > 1:
            seeker_ids = _shuffle(list(by_seeker.keys()), rng)
            target_val_size = _safe_val_count(len(clean), ratio)

            train: List[Sample] = []
            val: List[Sample] = []

            for seeker_id in seeker_ids:
                bucket = by_seeker[seeker_id]
                if len(val) < target_val_size:
                    val.extend(bucket)
                else:
                    train.extend(bucket)

            # 防止极端情况下一边为空
            if not val and len(train) > 1:
                val.append(train.pop(0))
            if not train and len(val) > 1:
                train.append(val.pop(0))

            # 若两边都有样本且标签分布可用，采用分组切分结果
            if train and val and (_has_both_labels(train) or _has_both_labels(val)):
                train = _shuffle(train, rng)
                val = _shuffle(val, rng)
                stats = {
                    "total": len(clean),
                    "train": len(train),
                    "val": len(val),
                    "train_pos_neg": _count_pos_neg(train),
                    "val_pos_neg": _count_pos_neg(val),
                    "strategy": "group_by_seeker",
                }
                return train, val, stats

    # 回退到分层切分
    train, val = _split_stratified(clean, ratio, rng)
    stats = {
        "total": len(clean),
        "train": len(train),
        "val": len(val),
        "train_pos_neg": _count_pos_neg(train),
        "val_pos_neg": _count_pos_neg(val),
        "strategy": "stratified_fallback",
    }
    return train, val, stats



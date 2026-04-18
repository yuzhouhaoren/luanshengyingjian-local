from __future__ import annotations
from dataclasses import dataclass
import importlib
from typing import List, Optional, Tuple

import numpy as np
from config import SETTINGS
from db.crud import MatchRecord, UserFeature, load_user_features, save_match_records
from model.llm_embedder import generate_match_reason


def _load_dual_tower_similarity():
    for module_name in ("model.dual_tower_model", "model.dual_tower"):
        try:
            module = importlib.import_module(module_name)
            func = getattr(module, "dual_tower_similarity", None)
            if callable(func):
                return func
        except Exception:
            continue
    return None


dual_tower_similarity = _load_dual_tower_similarity()


@dataclass(frozen=True)
class MatchEngineResult:
    # 单次匹配结果
    intent_type: str
    users_involved: int
    records_generated: int


#规范化意向类型名称，兼容历史字段值
def _normalize_intent_type(intent_type: str) -> str:
    text = str(intent_type or "").strip()
    if text in {"伴侣", "intent_伴侣"}:
        return "伴侣"
    if text in {"朋友", "志趣相投的朋友", "intent_志趣相投的朋友"}:
        return "朋友"
    return text


#将性别字段归一到有限集合，避免多种写法影响规则判断
def _normalize_gender(value: str) -> str:
    text = str(value or "").strip().lower()
    if text in {"男", "male", "m", "man", "男性"}:
        return "男"
    if text in {"女", "female", "f", "woman", "女性"}:
        return "女"
    return "unknown"


#判断 owner 的性取向是否接受 target，供伴侣匹配过滤使用
def _orientation_accepts_target(owner: UserFeature, target: UserFeature) -> bool:
    orientation = str(owner.sexual_orientation or "").strip().lower()
    # 伴侣匹配需要明确性取向
    if not orientation:
        return False

    owner_gender = _normalize_gender(owner.gender)
    target_gender = _normalize_gender(target.gender)
    if target_gender == "unknown":
        return False

    # 无性恋按严格策略只匹配同为无性恋用户
    if ("无性" in orientation) or ("asexual" in orientation):
        target_orientation = str(target.sexual_orientation or "").strip().lower()
        return ("无性" in target_orientation) or ("asexual" in target_orientation)

    if "异性" in orientation:
        if owner_gender == "unknown":
            return False
        return owner_gender != target_gender

    if "同性" in orientation:
        if owner_gender == "unknown":
            return False
        return owner_gender == target_gender

    if ("双" in orientation) or ("泛" in orientation) or ("bi" in orientation) or ("pan" in orientation):
        return True

    if ("喜欢男" in orientation) or ("男性" in orientation) or (orientation in {"男", "male"}):
        return target_gender == "男"

    if ("喜欢女" in orientation) or ("女性" in orientation) or (orientation in {"女", "female"}):
        return target_gender == "女"

    return True


#伴侣场景要求双向满足性取向过滤
def _is_partner_candidate_allowed(seeker: UserFeature, candidate: UserFeature) -> bool:
    # 伴侣匹配要求双方性取向都满足
    if seeker.intent_type != "伴侣" or candidate.intent_type != "伴侣":
        return False
    return _orientation_accepts_target(seeker, candidate) and _orientation_accepts_target(candidate, seeker)


#安全余弦相似度，自动处理空向量和维度不一致
def _cosine_similarity(vector_a: np.ndarray, vector_b: np.ndarray) -> Optional[float]:
    if vector_a.size == 0 or vector_b.size == 0:
        return None
    if int(vector_a.shape[0]) != int(vector_b.shape[0]):
        return None

    denominator = float(np.linalg.norm(vector_a) * np.linalg.norm(vector_b))
    if denominator <= 1e-8:
        return None

    score = float(np.dot(vector_a, vector_b) / denominator)
    return max(-1.0, min(1.0, score))


#使用双塔打分
def _compute_match_score(seeker: UserFeature, candidate: UserFeature) -> Optional[float]:
    if dual_tower_similarity is not None:
        try:
            score = dual_tower_similarity(
                seeker_profile_vector=seeker.profile_vector,
                seeker_intent_vector=seeker.vector,
                candidate_profile_vector=candidate.profile_vector,
                candidate_intent_vector=candidate.vector,
                embed_dim=int(getattr(SETTINGS, "dual_tower_embed_dim", 64)),
                seed=int(getattr(SETTINGS, "dual_tower_seed", 42)),
                profile_weight=float(getattr(SETTINGS, "dual_tower_profile_weight", 0.6)),
                intent_weight=float(getattr(SETTINGS, "dual_tower_intent_weight", 0.4)),
            )
            if score is not None:
                return max(-1.0, min(1.0, float(score)))
        except TypeError:
            try:
                score = dual_tower_similarity(seeker.vector, candidate.vector)
                if score is not None:
                    return max(-1.0, min(1.0, float(score)))
            except Exception:
                pass
        except Exception:
            pass

    return _cosine_similarity(seeker.vector, candidate.vector)


#为单个用户构建候选匹配记录
def _build_records_for_user(
    seeker: UserFeature,
    candidates: List[UserFeature],
    intent_type: str,
    top_k: int,
    apply_min_score: bool,
) -> List[MatchRecord]:
    scored: List[Tuple[float, UserFeature]] = []
    #关闭最低阈值时仅保留非负相关候选
    threshold = SETTINGS.min_match_score if apply_min_score else 0.0

    for candidate in candidates:
        if candidate.user_id == seeker.user_id:
            continue

        if intent_type == "伴侣" and not _is_partner_candidate_allowed(seeker, candidate):
            continue

        score = _compute_match_score(seeker, candidate)
        if score is None:
            continue

        # 关闭最低阈值时，仍然过滤掉负相关结果，避免出现明显反向推荐。
        if score < float(threshold):
            continue

        scored.append((score, candidate))

    if not scored:
        return []

    scored.sort(key=lambda item: item[0], reverse=True)
    selected = scored[: max(1, int(top_k))]

    records: List[MatchRecord] = []
    for score, candidate in selected:
        candidate_display_name = candidate.name or candidate.username or candidate.user_id

        #按配置决定理由生成策略：小模型或规则兜底
        if SETTINGS.use_llm_reason:
            reason = generate_match_reason(
                seeker_name=(seeker.name or seeker.username or seeker.user_id),
                candidate_name=candidate_display_name,
                intent_type=intent_type,
                match_score=float(score),
                seeker_profile_vector=seeker.profile_vector,
                candidate_profile_vector=candidate.profile_vector,
            )
        else:
            reason = (
                f"系统根据画像和意向向量匹配，推荐你优先了解{candidate_display_name}。"
            )

        records.append(
            MatchRecord(
                user_id=seeker.user_id,
                matched_user_id=candidate.user_id,
                matched_user_name=candidate_display_name,
                email=candidate.email,
                match_score=round(float(score), 4),
                intent_type=intent_type,
                reason=reason,
            )
        )

    return records


#对指定用户执行单次匹配并落库
def match_and_save_for_user(
    user_id: str,
    intent_type: str,
    apply_min_score: bool = False,
    top_k: int = 1,
    clear_existing_pending: bool = True,
) -> MatchEngineResult:
    normalized_intent = _normalize_intent_type(intent_type)
    features = load_user_features(intent_type=normalized_intent, only_pool_users=True)
    if not features:
        return MatchEngineResult(intent_type=normalized_intent, users_involved=0, records_generated=0)

    seeker = None
    for feature in features:
        if feature.user_id == user_id:
            seeker = feature
            break

    if seeker is None:
        return MatchEngineResult(intent_type=normalized_intent, users_involved=len(features), records_generated=0)

    records = _build_records_for_user(
        seeker=seeker,
        candidates=features,
        intent_type=normalized_intent,
        top_k=max(1, int(top_k)),
        apply_min_score=apply_min_score,
    )

    generated = save_match_records(records, clear_existing_pending=bool(clear_existing_pending))
    return MatchEngineResult(
        intent_type=normalized_intent,
        users_involved=len(features),
        records_generated=generated,
    )


#对某类意向用户执行批量匹配
def run_intent_matching(
    intent_type: str,
    apply_min_score: bool = False,
    top_k: Optional[int] = None,
) -> MatchEngineResult:
    normalized_intent = _normalize_intent_type(intent_type)
    features = load_user_features(intent_type=normalized_intent, only_pool_users=True)
    if len(features) <= 1:
        return MatchEngineResult(
            intent_type=normalized_intent,
            users_involved=len(features),
            records_generated=0,
        )

    max_top_k = max(1, int(top_k if top_k is not None else SETTINGS.top_k))
    all_records: List[MatchRecord] = []

    for seeker in features:
        all_records.extend(
            _build_records_for_user(
                seeker=seeker,
                candidates=features,
                intent_type=normalized_intent,
                top_k=max_top_k,
                apply_min_score=apply_min_score,
            )
        )

    generated = save_match_records(all_records, clear_existing_pending=True)
    return MatchEngineResult(
        intent_type=normalized_intent,
        users_involved=len(features),
        records_generated=generated,
    )


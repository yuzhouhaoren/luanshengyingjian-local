import numpy as np

def _to_ld_float_vector(vector) -> np.ndarray:
    if vector is None:
        return np.array([],dtype=np.float32)
    arr = np.asarray(vector,dtype= np.float32)

    if arr.ndim == 0:
        arr = arr.reshape(1)
    elif arr.ndim >1:
        arr = arr.reshape(-1)
    return arr

def _project_to_fixed_dim(vector, embed_dim:int,seed :int) -> np.ndarray:
    vec = _to_ld_float_vector(vector)

    if embed_dim<=0:
        return np.array([],dtype=np.float32)
    
    if vec.size == 0:
        return np.zeros(embed_dim,dtype=np.float32)
    
    dim_seed = int(seed) + int(vec.size) * 1089
    rng = np.random.default_rng(dim_seed)
    #生成确定性的投影矩阵
    projection = rng.standard_normal((vec.size,embed_dim)).astype(np.float32)

    out = np.matmul(vec, projection).astype(np.float32)

    norm = float(np.linalg.norm(out))
    if norm <= 1e-8:
        return np.zeros(embed_dim,dtype=np.float32)

    return out / norm

def _safe_cosine_similarity(vector_a,vector_b) -> float:
    a = _to_ld_float_vector(vector_a)
    b = _to_ld_float_vector(vector_b)

    if a.size==0 or b.size == 0:
        return 0.0
    if int(a.shape[0]) != int(b.shape[0]):
        return 0.0
    #计算a,b模长的积
    denominator = float(np.linalg.norm(a)*np.linalg.norm(b))
    if denominator <= 1e-8:
        return 0.0
    #计算余弦相似度
    score = float(np.dot(a,b) / denominator)

    if score>1.0:
        return 1.0
    if score< -1.0:
        return -1.0
    return score


def _normalize_weights(profile_weight: float, intent_weight: float) -> tuple[float, float]:
    try:
        p = float(profile_weight)
    except (TypeError, ValueError):
        p = 0.6

    try:
        i = float(intent_weight)
    except (TypeError, ValueError):
        i = 0.4

    # 权重不允许为负，先裁剪到非负区间。
    p = max(0.0, p)
    i = max(0.0, i)

    total = p + i
    if total <= 1e-8:
        return 0.6, 0.4

    return p / total, i / total

def dual_tower_similarity(
        seeker_profile_vector,
        seeker_intent_vector,
        candidate_profile_vector,
        candidate_intent_vector,
        embed_dim: int = 64,
        seed:int = 42,
        profile_weight: float = 0.6,
        intent_weight : float = 0.4,
) -> float:
    dim = int(embed_dim)
    if dim <= 0:
        dim = 64

    pw, iw = _normalize_weights(profile_weight, intent_weight)

    seeker_intent_arr = _to_ld_float_vector(seeker_intent_vector)
    candidate_intent_arr = _to_ld_float_vector(candidate_intent_vector)
    seeker_profile_arr = _to_ld_float_vector(seeker_profile_vector)
    candidate_profile_arr = _to_ld_float_vector(candidate_profile_vector)

    has_seeker_intent = seeker_intent_arr.size > 0
    has_candidate_intent = candidate_intent_arr.size > 0
    has_candidate_profile = candidate_profile_arr.size > 0
    has_seeker_profile = seeker_profile_arr.size > 0

    # 主信号：A 的意向偏好是否匹配 B 的画像特征（方向性 A->B）。
    if has_seeker_intent:
        seeker_intent_proj = _project_to_fixed_dim(seeker_intent_arr, dim, int(seed) + 11)
    else:
        seeker_intent_proj = np.zeros(dim, dtype=np.float32)

    if has_candidate_profile:
        candidate_profile_proj = _project_to_fixed_dim(candidate_profile_arr, dim, int(seed) + 101)
        preference_score = _safe_cosine_similarity(seeker_intent_proj, candidate_profile_proj)
    else:
        preference_score = 0.0

    # 辅助信号：双方意向一致度，作为方向主信号的稳定补充。
    if has_candidate_intent:
        candidate_intent_proj = _project_to_fixed_dim(candidate_intent_arr, dim, int(seed) + 41)
        intent_score = _safe_cosine_similarity(seeker_intent_proj, candidate_intent_proj)
    else:
        intent_score = 0.0

    if has_seeker_intent and has_candidate_profile and has_candidate_intent:
        score = (pw * preference_score) + (iw * intent_score)
    elif has_seeker_intent and has_candidate_profile:
        score = preference_score
    elif has_seeker_intent and has_candidate_intent:
        score = intent_score
    elif has_seeker_profile and has_candidate_profile:
        # seeker 缺少意向时，退化到画像相似，尽量保证可用性。
        seeker_profile_proj = _project_to_fixed_dim(seeker_profile_arr, dim, int(seed) + 131)
        candidate_profile_proj = _project_to_fixed_dim(candidate_profile_arr, dim, int(seed) + 131)
        score = _safe_cosine_similarity(seeker_profile_proj, candidate_profile_proj)
    else:
        score = 0.0

    if score > 1.0:
        return 1.0
    if score < -1.0:
        return -1.0
    return float(score)

    
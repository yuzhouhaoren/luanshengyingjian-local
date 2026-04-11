from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from config import SETTINGS

# 基础画像向量键顺序
PROFILE_BASE_KEYS = (
    "E",
    "O",
    "C",
    "A",
    "N",
)

# 基础画像向量键顺序
PROFILE_BASE_KEYS_LEGACY = (
    "extraversion",
    "openness",
    "conscientiousness",
    "agreeableness",
    "neuroticism",
)

# 意向向量配置：伴侣 7 维，朋友 6 维
INTENT_VECTOR_CONFIG = {
    "伴侣": {
        "score_key": "intent_伴侣",
        "dims": ("S", "I", "R", "M", "D", "E", "N"),
        "pool_col": "in_partner_pool",
    },
    "朋友": {
        "score_key": "intent_志趣相投的朋友",
        "dims": ("I", "V", "P", "L", "E", "G"),
        "pool_col": "in_friend_pool",
    },
}

# 优先读取这些向量列
VECTOR_COLUMN_CANDIDATES = (
    "feature_vector",
    "profile_vector",
    "embedding",
    "user_vector",
    "vector",
)


@dataclass(frozen=True)
class UserFeature:
    # 单个用户用于匹配计算的特征对象
    user_id: str
    username: str
    name: str
    email: str
    gender: str
    sexual_orientation: str
    profile_vector: np.ndarray
    vector: np.ndarray
    vector_source: str
    intent_type: str


@dataclass(frozen=True)
class MatchRecord:
    # 写入 match_results 的记录对象
    user_id: str
    matched_user_id: str
    matched_user_name: str
    email: str
    match_score: float
    intent_type: str = "朋友"
    reason: Optional[str] = None


@contextmanager
def get_db_connection():
    # 统一数据库连接上下文
    conn = sqlite3.connect(str(SETTINGS.db_path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    # 读取表字段
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    names = set()
    for row in rows:
        if isinstance(row, sqlite3.Row):
            names.add(str(row["name"]))
        else:
            names.add(str(row[1]))
    return names


#读取表字段类型，用于兼容不同数据库迁移版本
def _table_column_types(conn: sqlite3.Connection, table_name: str) -> Dict[str, str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    result: Dict[str, str] = {}
    for row in rows:
        if isinstance(row, sqlite3.Row):
            name = str(row["name"])
            col_type = str(row["type"] or "")
        else:
            name = str(row[1])
            col_type = str(row[2] or "")
        result[name] = col_type
    return result


#从 sqlite Row 中安全取字段，字段缺失时返回默认值
def _row_get(row: sqlite3.Row, key: str, default: Any = None) -> Any:
    return row[key] if key in row.keys() else default


def _is_true(value: Any) -> bool:
    # 兼容 bool / 数字 / 字符串三类真值判断
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


#安全转 float，非法值统一返回 None 交由上游处理
def _safe_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


#标准化意向名称，兼容历史字段和值
def _normalize_intent_type(intent_type: Optional[str]) -> Optional[str]:
    if intent_type is None:
        return None

    text = str(intent_type).strip()
    if text in {"伴侣", "intent_伴侣"}:
        return "伴侣"
    if text in {"朋友", "志趣相投的朋友", "intent_志趣相投的朋友"}:
        return "朋友"
    return None


#将 profile_scores 字段解析为 dict，兼容 bytes 与 JSON 字符串
def _parse_profile_scores(raw: Any) -> Optional[Dict[str, Any]]:
    if raw is None:
        return None

    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="ignore")

    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None
        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            return None

    if isinstance(raw, dict):
        return raw
    return None


#按给定 key 顺序提取向量，任何维度缺失都视为不可用
def _extract_vector_by_keys(raw: Dict[str, Any], keys: Sequence[str]) -> Optional[np.ndarray]:
    values: List[float] = []
    for key in keys:
        v = _safe_float(raw.get(key))
        if v is None:
            return None
        values.append(v)

    if not values:
        return None
    return np.asarray(values, dtype=np.float32)


def _to_vector(raw: Any) -> Optional[np.ndarray]:
    # 将数据库中的不同格式转换为 np.ndarray
    if raw is None:
        return None

    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="ignore")

    # 字符串可能是 JSON，也可能是 "1,2,3"
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None
        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            parts = [item.strip() for item in text.split(",") if item.strip()]
            values: List[float] = []
            for item in parts:
                v = _safe_float(item)
                if v is None:
                    return None
                values.append(v)
            if not values:
                return None
            return np.asarray(values, dtype=np.float32)

    if isinstance(raw, list):
        values: List[float] = []
        for item in raw:
            v = _safe_float(item)
            if v is None:
                return None
            values.append(v)
        if not values:
            return None
        return np.asarray(values, dtype=np.float32)

    if isinstance(raw, dict):
        # 回退策略：按 key 排序提取数值字段
        values = []
        for key in sorted(raw.keys()):
            v = _safe_float(raw.get(key))
            if v is not None:
                values.append(v)
        if not values:
            return None
        return np.asarray(values, dtype=np.float32)

    return None


def _normalize_vector(vector: np.ndarray) -> np.ndarray:
    # 归一化后再做点积，可以直接得到余弦相似度
    norm = float(np.linalg.norm(vector))
    if norm <= 0:
        return vector.astype(np.float32)
    return (vector / norm).astype(np.float32)


def ensure_match_results_table(conn: sqlite3.Connection) -> None:
    #避免独立运行 pairModel 时找不到表
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS match_results (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            matched_user_id TEXT,
            matched_user_name TEXT,
            match_score REAL,
            intent_type TEXT,
            email TEXT,
            status TEXT DEFAULT 'pending',
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


#从候选列名中选择当前 users 表可用的向量列
def _pick_vector_column(user_columns: set[str]) -> Optional[str]:
    for col in VECTOR_COLUMN_CANDIDATES:
        if col in user_columns:
            return col
    return None


def load_user_features(
    intent_type: Optional[str] = None,
    only_pool_users: bool = False,
) -> List[UserFeature]:
    # 从 users 表读取用户向量，按意向类型提取固定维度
    normalized_intent = _normalize_intent_type(intent_type)
    if normalized_intent is None:
        return []

    intent_config = INTENT_VECTOR_CONFIG[normalized_intent]

    with get_db_connection() as conn:
        user_columns = _table_columns(conn, "users")
        if not user_columns:
            return []

        base_fields = ["id", "username", "name", "email", "gender", "sexual_orientation"]
        vector_col = _pick_vector_column(user_columns)
        profile_col = "profile_scores" if "profile_scores" in user_columns else None

        optional_fields: List[str] = []
        if vector_col:
            optional_fields.append(vector_col)
        if profile_col and profile_col not in optional_fields:
            optional_fields.append(profile_col)
        pool_col = intent_config["pool_col"]
        if pool_col in user_columns:
            optional_fields.append(pool_col)

        select_fields = base_fields + optional_fields
        sql = f"SELECT {', '.join(select_fields)} FROM users"
        rows = conn.execute(sql).fetchall()

        results: List[UserFeature] = []
        for row in rows:
            # 若按池过滤，则只保留对应池内用户
            if only_pool_users and pool_col in user_columns:
                if not _is_true(_row_get(row, pool_col, False)):
                    continue

            source = profile_col or ""
            profile_vector = None
            intent_vector = None

            profile_scores = _parse_profile_scores(_row_get(row, profile_col)) if profile_col else None
            if profile_scores is not None:
                profile_vector = _extract_vector_by_keys(profile_scores, PROFILE_BASE_KEYS)
                if profile_vector is None:
                    profile_vector = _extract_vector_by_keys(profile_scores, PROFILE_BASE_KEYS_LEGACY)

                raw_intent_scores = profile_scores.get(intent_config["score_key"])
                if isinstance(raw_intent_scores, dict):
                    intent_vector = _extract_vector_by_keys(raw_intent_scores, intent_config["dims"])

            # 回退：若 profile_scores 尚未准备好，可临时使用向量列。
            if intent_vector is None and vector_col:
                intent_vector = _to_vector(_row_get(row, vector_col))
                source = vector_col

            if intent_vector is None or intent_vector.size == 0:
                continue

            if profile_vector is None or profile_vector.size == 0:
                profile_vector = np.asarray([], dtype=np.float32)
            else:
                profile_vector = _normalize_vector(profile_vector)

            intent_vector = _normalize_vector(intent_vector)

            results.append(
                UserFeature(
                    user_id=str(_row_get(row, "id", "")),
                    username=str(_row_get(row, "username", "") or ""),
                    name=str(_row_get(row, "name", "") or ""),
                    email=str(_row_get(row, "email", "") or ""),
                    gender=str(_row_get(row, "gender", "") or ""),
                    sexual_orientation=str(_row_get(row, "sexual_orientation", "") or ""),
                    profile_vector=profile_vector,
                    vector=intent_vector,
                    vector_source=source,
                    intent_type=normalized_intent,
                )
            )

        return results


def save_match_records(
    records: Sequence[MatchRecord],
    clear_existing_pending: bool = True,
) -> int:
    # 批量写入匹配结果
    if not records:
        return 0

    with get_db_connection() as conn:
        ensure_match_results_table(conn)
        columns = _table_columns(conn, "match_results")
        column_types = _table_column_types(conn, "match_results")
        if not columns:
            return 0

        if clear_existing_pending and "status" in columns:
            user_ids = sorted({item.user_id for item in records if item.user_id})
            if user_ids:
                placeholders = ",".join("?" for _ in user_ids)
                conn.execute(
                    f"DELETE FROM match_results WHERE status = 'pending' AND user_id IN ({placeholders})",
                    user_ids,
                )

        ordered_candidates = [
            "id",
            "user_id",
            "matched_user_id",
            "matched_user_name",
            "match_score",
            "intent_type",
            "email",
            "status",
            "reason",
        ]
        insert_columns = [col for col in ordered_candidates if col in columns]

        #兼容已有库：若 id 为 INTEGER PRIMARY KEY，则不显式插入字符串 id。
        if "id" in insert_columns:
            id_type = str(column_types.get("id", "")).upper()
            if "INT" in id_type:
                insert_columns = [col for col in insert_columns if col != "id"]

        if not insert_columns:
            return 0

        placeholders = ",".join("?" for _ in insert_columns)
        sql = f"INSERT INTO match_results ({', '.join(insert_columns)}) VALUES ({placeholders})"

        for item in records:
            values: List[Any] = []
            for col in insert_columns:
                if col == "id":
                    values.append(f"mr_{uuid.uuid4().hex[:16]}")
                elif col == "user_id":
                    values.append(item.user_id)
                elif col == "matched_user_id":
                    values.append(item.matched_user_id)
                elif col == "matched_user_name":
                    values.append(item.matched_user_name)
                elif col == "match_score":
                    values.append(float(item.match_score))
                elif col == "intent_type":
                    values.append(item.intent_type)
                elif col == "email":
                    values.append(item.email)
                elif col == "status":
                    values.append("pending")
                elif col == "reason":
                    values.append(item.reason or "")
            conn.execute(sql, values)

        conn.commit()

    return len(records)


def fetch_user_intent_answers(user_id: str, intent_type: str) -> Optional[str]:
    # 优先兼容当前后端：users.partner_intent_answers / users.friend_intent_answers
    normalized_intent = _normalize_intent_type(intent_type)

    with get_db_connection() as conn:
        user_cols = _table_columns(conn, "users")
        if user_cols:
            if normalized_intent == "伴侣" and "partner_intent_answers" in user_cols:
                row = conn.execute(
                    """
                    SELECT partner_intent_answers AS answers
                    FROM users
                    WHERE id = ?
                    LIMIT 1
                    """,
                    (user_id,),
                ).fetchone()
                if row is not None:
                    value = str(_row_get(row, "answers", "") or "").strip()
                    if value:
                        return value

            if normalized_intent == "朋友" and "friend_intent_answers" in user_cols:
                row = conn.execute(
                    """
                    SELECT friend_intent_answers AS answers
                    FROM users
                    WHERE id = ?
                    LIMIT 1
                    """,
                    (user_id,),
                ).fetchone()
                if row is not None:
                    value = str(_row_get(row, "answers", "") or "").strip()
                    if value:
                        return value

        # 回退兼容旧表结构：user_intents
        table_cols = _table_columns(conn, "user_intents")
        if not table_cols or not {"user_id", "intent_type", "answers"}.issubset(table_cols):
            return None

        query_intent = intent_type
        if normalized_intent == "朋友":
            # 旧数据中朋友意向可能存成“志趣相投的朋友”
            row = conn.execute(
                """
                SELECT answers
                FROM user_intents
                WHERE user_id = ? AND intent_type IN ('朋友', '志趣相投的朋友', 'intent_志趣相投的朋友')
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        elif normalized_intent == "伴侣":
            row = conn.execute(
                """
                SELECT answers
                FROM user_intents
                WHERE user_id = ? AND intent_type IN ('伴侣', 'intent_伴侣')
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT answers
                FROM user_intents
                WHERE user_id = ? AND intent_type = ?
                LIMIT 1
                """,
                (user_id, query_intent),
            ).fetchone()

        if row is None:
            return None
        return str(_row_get(row, "answers", "") or "")


def db_health() -> Dict[str, Any]:
    # 健康检查：数据库路径 + users 数量 + match_results 数量
    with get_db_connection() as conn:
        ensure_match_results_table(conn)
        user_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        match_count = conn.execute("SELECT COUNT(*) AS c FROM match_results").fetchone()["c"]
    return {
        "db_path": str(SETTINGS.db_path),
        "users": int(user_count),
        "match_results": int(match_count),
    }
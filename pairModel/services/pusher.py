from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib import error as urllib_error
from urllib import request as urllib_request

from config import SETTINGS
from db.crud import get_db_connection, ensure_match_results_table


LOGGER = logging.getLogger(__name__)

_PUSH_ENDPOINT_AVAILABLE: Optional[bool] = None


@dataclass(frozen=True)
class PendingPushItem:
	record_id: str
	user_id: str
	matched_user_id: str
	matched_user_name: str
	match_score: float
	intent_type: str
	email: str


#从 sqlite Row 安全取值，缺字段时返回默认值
def _row_get(row: Any, key: str, default: Any = None) -> Any:
	if key in row.keys():
		return row[key]
	return default


#读取指定表的字段名集合，用于做结构兼容检查
def _table_columns(table_name: str) -> set[str]:
	with get_db_connection() as conn:
		rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()

	names = set()
	for row in rows:
		names.add(str(row["name"]) if hasattr(row, "keys") else str(row[1]))
	return names


#拼接推送目标地址
def _build_push_url() -> str:
	return f"{SETTINGS.push_base_url.rstrip('/')}{SETTINGS.push_endpoint}"


#标记推送端点不可用，避免后续重复无效请求
def _mark_endpoint_unavailable() -> None:
	global _PUSH_ENDPOINT_AVAILABLE
	previous_state = _PUSH_ENDPOINT_AVAILABLE
	_PUSH_ENDPOINT_AVAILABLE = False
	if previous_state is not False:
		LOGGER.info("push endpoint is unavailable, switching to db-only mode")


#读取待推送的 pending 匹配记录，可按用户过滤
def _load_pending_matches(limit: int = 20, user_id: Optional[str] = None) -> List[PendingPushItem]:
	columns = _table_columns("match_results")
	required = {
		"id",
		"user_id",
		"matched_user_id",
		"matched_user_name",
		"match_score",
		"intent_type",
		"email",
		"status",
	}
	if not required.issubset(columns):
		return []

	where_clauses = ["status = 'pending'"]
	params: List[Any] = []
	if user_id:
		where_clauses.append("user_id = ?")
		params.append(str(user_id))

	params.append(max(1, int(limit)))
	where_sql = " AND ".join(where_clauses)

	with get_db_connection() as conn:
		ensure_match_results_table(conn)
		rows = conn.execute(
			f"""
			SELECT id, user_id, matched_user_id, matched_user_name, match_score, intent_type, email
			FROM match_results
			WHERE {where_sql}
			ORDER BY match_score DESC, created_at DESC
			LIMIT ?
			""",
			params,
		).fetchall()

	items: List[PendingPushItem] = []
	for row in rows:
		items.append(
			PendingPushItem(
				record_id=str(_row_get(row, "id", "") or ""),
				user_id=str(_row_get(row, "user_id", "") or ""),
				matched_user_id=str(_row_get(row, "matched_user_id", "") or ""),
				matched_user_name=str(_row_get(row, "matched_user_name", "") or ""),
				match_score=float(_row_get(row, "match_score", 0.0) or 0.0),
				intent_type=str(_row_get(row, "intent_type", "") or ""),
				email=str(_row_get(row, "email", "") or ""),
			)
		)

	return items


#推送单条记录到后端接口，并返回成功标记与消息
def _push_item(item: PendingPushItem) -> tuple[bool, str]:
	global _PUSH_ENDPOINT_AVAILABLE

	if _PUSH_ENDPOINT_AVAILABLE is False:
		#端点已确认缺失时直接返回，避免重复网络开销
		return False, "endpoint_missing"

	payload = {
		"record_id": item.record_id,
		"user_id": item.user_id,
		"matched_user_id": item.matched_user_id,
		"matched_user_name": item.matched_user_name,
		"match_score": item.match_score,
		"intent_type": item.intent_type,
		"email": item.email,
	}

	body = json.dumps(payload).encode("utf-8")
	req = urllib_request.Request(
		_build_push_url(),
		data=body,
		headers={"Content-Type": "application/json"},
		method="POST",
	)

	try:
		with urllib_request.urlopen(req, timeout=max(1, int(SETTINGS.push_timeout_seconds))) as response:
			status = int(getattr(response, "status", 200))
			if 200 <= status < 300:
				_PUSH_ENDPOINT_AVAILABLE = True
				return True, "ok"

			raw = response.read().decode("utf-8", errors="ignore")
			text = raw.strip().replace("\n", " ")
			return False, f"http_{status}: {text[:160]}"
	except urllib_error.HTTPError as exc:
		if int(exc.code) == 404:
			#后端未实现推送接口时进入降级模式
			_mark_endpoint_unavailable()
			return False, "endpoint_missing"

		raw = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else ""
		text = raw.strip().replace("\n", " ")
		return False, f"http_{int(exc.code)}: {text[:160]}"
	except urllib_error.URLError as exc:
		return False, str(exc.reason)


#批量推送 pending 匹配结果，返回执行统计
def push_pending_once(limit: int = 20, user_id: Optional[str] = None) -> Dict[str, Any]:
	# 推送 pending 记录到后端接口，记录状态仍保持 pending，避免影响前端读取逻辑
	pending_items = _load_pending_matches(limit=limit, user_id=user_id)
	if not pending_items:
		return {
			"status": "empty",
			"total": 0,
			"success": 0,
			"failed": 0,
			"details": [],
		}

	if not SETTINGS.enable_push:
		return {
			"status": "disabled",
			"total": len(pending_items),
			"success": 0,
			"failed": 0,
			"details": [],
		}

	if _PUSH_ENDPOINT_AVAILABLE is False:
		return {
			"status": "endpoint_missing",
			"total": len(pending_items),
			"success": 0,
			"failed": 0,
			"details": [
				{
					"record_id": "",
					"ok": "False",
					"message": "backend push endpoint not found; db-only mode",
				}
			],
		}

	success = 0
	failed = 0
	details: List[Dict[str, str]] = []

	for item in pending_items:
		ok, message = _push_item(item)
		if message == "endpoint_missing":
			return {
				"status": "endpoint_missing",
				"total": len(pending_items),
				"success": success,
				"failed": failed,
				"details": [
					{
						"record_id": item.record_id,
						"ok": "False",
						"message": "backend push endpoint not found; db-only mode",
					}
				],
			}

		if ok:
			success += 1
		else:
			failed += 1
			LOGGER.warning("push failed record_id=%s reason=%s", item.record_id, message)

		details.append(
			{
				"record_id": item.record_id,
				"ok": str(ok),
				"message": message,
			}
		)

	return {
		"status": "ok",
		"total": len(pending_items),
		"success": success,
		"failed": failed,
		"details": details,
	}
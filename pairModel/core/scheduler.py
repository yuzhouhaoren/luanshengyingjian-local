from __future__ import annotations

import logging
from typing import Dict,List,Tuple
from apscheduler.schedulers.background import BackgroundScheduler

from config import SETTINGS
from core.matcher import match_and_save_for_user
from db.crud import load_user_features
from services.pusher import push_pending_once

LOGGER = logging.getLogger(__name__)

#构建批处理队列：收集两个池里全部可计算用户
def _build_candidate_queue() -> List[Tuple[str,str]]:
    #从两个池中选取候选用户，队列元素：user_id,intent_type
    queue : List[Tuple[str,str]] = []
    seen = set()

    for intent_type in ("伴侣","朋友"):
        features = load_user_features(intent_type=intent_type,only_pool_users=True)
        for feature in features:
            key = (feature.user_id,intent_type)
            if key in seen:
                continue
            seen.add(key)
            queue.append(key)
    return queue


#执行一次调度 tick：批量处理所有用户，不按先后轮询
def run_match_once(apply_min_score: bool = False) -> Dict[str,object]:
    queue = _build_candidate_queue()
    if not queue:
        return{
            "status": "empty",
            "queue_pairs": 0,
            "users_involved": 0,
            "records_generated": 0,
        }

    users_involved = set()
    processed_by_intent = {"伴侣": 0, "朋友": 0}
    generated_by_intent = {"伴侣": 0, "朋友": 0}
    total_generated = 0

    for user_id, intent_type in queue:
        clear_existing_pending = user_id not in users_involved
        result = match_and_save_for_user(
            user_id=user_id,
            intent_type=intent_type,
            apply_min_score=apply_min_score,
            top_k=1,
            clear_existing_pending=clear_existing_pending,
        )
        users_involved.add(user_id)
        processed_by_intent[intent_type] = processed_by_intent.get(intent_type, 0) + 1
        generated_by_intent[intent_type] = generated_by_intent.get(intent_type, 0) + int(result.records_generated)
        total_generated += int(result.records_generated)

    if total_generated > 0 and SETTINGS.enable_push:
        # 只推送本轮新生成的记录，避免把历史 pending 误当成本轮结果重复推送。
        push_result = push_pending_once(limit=total_generated)
    else:
        push_result = {
            "status": "disabled" if not SETTINGS.enable_push else "skipped",
            "total": 0,
            "success": 0,
            "failed": 0,
            "details": [],
        }

    LOGGER.info(
        "match tick batch apply_min_score=%s users=%s pairs=%s generated=%s by_intent=%s",
        apply_min_score,
        len(users_involved),
        len(queue),
        total_generated,
        generated_by_intent,
    )
    LOGGER.info(
        "push tick batch status=%s total=%s success=%s failed=%s",
        push_result.get("status"),
        push_result.get("total",0),
        push_result.get("success",0),
        push_result.get("failed",0),
    )
    return{
        "status": "ok",
        "queue_pairs": len(queue),
        "users_involved": len(users_involved),
        "processed_by_intent": processed_by_intent,
        "generated_by_intent": generated_by_intent,
        "records_generated": total_generated,
        "push": push_result,
    }
    
#创建 APScheduler 调度器并注册匹配任务
def create_scheduler(apply_min_score: bool = False) -> BackgroundScheduler:
    days = str(getattr(SETTINGS, "scheduler_cron_days", "tue,fri") or "tue,fri").strip().lower()
    hour = max(0, min(23, int(getattr(SETTINGS, "scheduler_cron_hour", 0))))
    minute = max(0, min(59, int(getattr(SETTINGS, "scheduler_cron_minute", 0))))
    scheduler = BackgroundScheduler(timezone=getattr(SETTINGS, "scheduler_timezone", "Asia/Shanghai"))
    scheduler.add_job(
        run_match_once,
        trigger="cron",
        day_of_week=days,
        hour=hour,
        minute=minute,
        kwargs={"apply_min_score": apply_min_score},
        id="pairmodel_match_tick",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=6 * 60 * 60,
    )
    return scheduler

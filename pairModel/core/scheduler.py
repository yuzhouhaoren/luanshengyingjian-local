from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict,List,Tuple
from apscheduler.schedulers.background import BackgroundScheduler

from config import SETTINGS
from core.matcher import match_and_save_for_user
from db.crud import load_user_features
from services.pusher import push_pending_once

LOGGER = logging.getLogger(__name__)

@dataclass
class _RoundRobinState:
    cursor: int = 0

_STATE = _RoundRobinState()

#构建轮转队列：从两个池中提取可计算用户
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


#执行一次调度 tick：挑选一个用户做匹配并按需推送
def run_match_once(apply_min_score: bool = False) -> Dict[str,object]:
    #单次匹配，前期apply_min_score=false,只按时间推送，后期可将false改为true
    queue = _build_candidate_queue()
    if not queue:
        return{
            "status": "empty",
            "queue_size": 0,
            "records_generated": 0,
        }
    
    #轮转游标，避免总是命中同一个用户
    index = _STATE.cursor % len(queue)
    _STATE.cursor = (index + 1)%len(queue)

    user_id,intent_type = queue[index]
    result = match_and_save_for_user(
        user_id=user_id,
        intent_type=intent_type,
        apply_min_score=apply_min_score,
        top_k=1,  # 前期先固定每次推荐 1 人
    )
    
    if result.records_generated > 0 and SETTINGS.enable_push:
        push_result = push_pending_once(limit=1, user_id=user_id)
    else:
        push_result = {
            "status": "disabled" if not SETTINGS.enable_push else "skipped",
            "total": 0,
            "success": 0,
            "failed": 0,
            "details": [],
        }

    LOGGER.info(
        "match tick user=%s intent=%s apply_min_score=%s generated=%s",
        user_id,
        intent_type,
        apply_min_score,
        result.records_generated,
    )
    LOGGER.info(
        "push tick user=%s status=%s total=%s success=%s failed=%s",
        user_id,
        push_result.get("status"),
        push_result.get("total",0),
        push_result.get("success",0),
        push_result.get("failed",0),
    )
    return{
        "status": "ok",
        "user_id": user_id,
        "intent_type": intent_type,
        "queue_size": len(queue),
        "records_generated": result.records_generated,
        "push": push_result,
    }
    
#创建 APScheduler 调度器并注册匹配任务
def create_scheduler(apply_min_score: bool = False) -> BackgroundScheduler:
    # 创建调度器，真正开关在这里传入
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_match_once,
        trigger="interval",
        minutes=max(1, int(SETTINGS.scheduler_interval_minutes)),
        kwargs={"apply_min_score": apply_min_score},
        id="pairmodel_match_tick",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=30,
    )
    return scheduler

from __future__ import annotations

import logging
import time

from config import SETTINGS
from core.scheduler import create_scheduler, run_match_once
from db.crud import db_health


def main() -> None:
    #读取运行策略配置
    apply_min_score = bool(SETTINGS.apply_min_score)
    run_once = bool(SETTINGS.run_once)
    run_once_limit = max(1, int(SETTINGS.run_once_times))

    #初始化日志格式
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        health = db_health()
        logger.info(
            "pairModel db health path=%s users=%s match_results=%s",
            health.get("db_path"),
            health.get("users"),
            health.get("match_results"),
        )
    except Exception as exc:
        logger.exception("pairModel db health check failed: %s", exc)

    if run_once:
        #单次模式用于本地调试、压测和手动触发
        logger.info(
            "pairModel run once mode enabled, apply_min_score=%s, times=%s",
            apply_min_score,
            run_once_limit,
        )
        for _ in range(run_once_limit):
            result = run_match_once(apply_min_score=apply_min_score)
            logger.info("pairModel run once result=%s", result)
        return

    #常驻模式启动定时调度器
    scheduler = create_scheduler(apply_min_score=apply_min_score)
    scheduler.start()
    logger.info(
        "pairModel scheduler started, apply_min_score=%s, interval_minutes=%s",
        apply_min_score,
        SETTINGS.scheduler_interval_minutes,
    )

    try:
        #保持主线程存活，直到收到中断信号
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("pairModel scheduler stopping...")
    finally:
        #确保退出时释放调度器资源
        scheduler.shutdown(wait=False)
        logger.info("pairModel scheduler stopped")


if __name__ == "__main__":
    main()
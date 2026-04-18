import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

#获取根目录
PAIRMODEL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PAIRMODEL_DIR.parent

#允许从根目录.evn读取配置
load_dotenv(PROJECT_ROOT / ".env")


#将读取配置字符串转换为对于类型，如果失败返回默认值
def _to_int (value : str, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
    
#将读取配置字符串转换为浮点数，如果失败返回默认值
def _to_float (value: str, default: float) -> float:
    try:
        return float(value)
    except  (TypeError, ValueError):
        return default

#将读取配置字符串转换为布尔值
def _to_bool (value: str, default: bool) -> bool:
    if value is None:
        return default
    v= value.strip().lower()
    if v in("1","true","yes","on"):
        return True
    if v in("0","false","no","off"):
        return False
    return default

#寻找数据库路径
def _default_db_path() ->Path:
    candidatas =[
        PROJECT_ROOT / "dating.db",
        PROJECT_ROOT / "backend" / "dating.db",
    ]
    for item in candidatas:
        if item.exists():
            return item
    return candidatas[0]

@dataclass(frozen=True)
class Settings:
    app_env: str   #运行环境
    db_path: Path  #数据库路径
    
    #匹配计算参数
    top_k: int  #每个用户至多保留匹配对象
    min_match_score: float        #匹配分数阈值
    #特征权重
    vector_profile_weight: float  
    vector_text_weight: float    
    
    #调度参数
    #匹配间隔
    scheduler_interval_minutes: int

    #运行策略
    apply_min_score: bool         #是否启用最低相似度阈值
    run_once: bool                #是否只运行一次后退出
    run_once_times: int           #一次性运行的轮数
    
    #推送参数
    enable_push: bool   #是否推送
    push_base_url: str   #推送目标地址
    push_endpoint: str
    push_timeout_seconds: int     #推送请求超时

    #是否启用小模型生成推荐理由
    use_llm_reason: bool

#获取配置
def get_settings() ->Settings:
    #优先读取环境变量数据库路径，未配置时走自动探测
    db_path_env = os.getenv("PAIRMODEL_DB_PATH","").strip()
    db_path = Path(db_path_env) if db_path_env else _default_db_path()
    
    #统一在这里组装所有配置，业务代码只依赖 SETTINGS 即可
    return Settings(
        app_env=os.getenv("PAIRMODEL_ENV", "dev"),
        db_path=db_path,

        top_k=_to_int(os.getenv("PAIRMODEL_TOP_K", "10"), 10),
        min_match_score=_to_float(os.getenv("PAIRMODEL_MIN_SCORE", "0.45"), 0.45),
        vector_profile_weight=_to_float(os.getenv("PAIRMODEL_PROFILE_WEIGHT", "0.7"), 0.7),
        vector_text_weight=_to_float(os.getenv("PAIRMODEL_TEXT_WEIGHT", "0.3"), 0.3),

        scheduler_interval_minutes=_to_int(os.getenv("PAIRMODEL_SCHEDULE_MINUTES", "7200"), 7200),

        apply_min_score=_to_bool(os.getenv("PAIRMODEL_APPLY_MIN_SCORE", "false"), False),
        run_once=_to_bool(os.getenv("PAIRMODEL_RUN_ONCE", "false"), False),
        run_once_times=max(1, _to_int(os.getenv("PAIRMODEL_RUN_ONCE_TIMES", "1"), 1)),

        enable_push=_to_bool(os.getenv("PAIRMODEL_ENABLE_PUSH", "false"), False),
        push_base_url=os.getenv("PAIRMODEL_PUSH_BASE_URL", "http://127.0.0.1:5000"),
        push_endpoint=os.getenv("PAIRMODEL_PUSH_ENDPOINT", "/api/match/push"),
        push_timeout_seconds=_to_int(os.getenv("PAIRMODEL_PUSH_TIMEOUT", "8"), 8),

        use_llm_reason=_to_bool(os.getenv("PAIRMODEL_USE_LLM_REASON", "false"), False),
    )


#模块加载时初始化配置，供其他模块直接复用
SETTINGS = get_settings()
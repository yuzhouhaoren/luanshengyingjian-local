from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import torch

from .losses import LossConfig
from .model_net import DualTowerTrainConfig, DualTowerTrainModel


# 确保目录存在，不存在则递归创建
def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


# 将对象递归转换为可 JSON 序列化的数据结构
def _to_jsonable(obj: Any) -> Any:
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    return obj


# 保存训练产物：模型参数、配置和统计信息
def save_training_artifacts(
    save_dir: str | Path,
    model: DualTowerTrainModel,
    model_config: DualTowerTrainConfig,
    loss_config: LossConfig,
    train_stats: Dict[str, Any],
    history: Optional[list[dict[str, Any]]] = None,
    extra_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    root = Path(save_dir)
    _ensure_dir(root)

    model_path = root / "model.pt"
    config_path = root / "config.json"
    stats_path = root / "stats.json"

    # 模型参数
    torch.save(model.state_dict(), model_path)

    # 训练配置
    config_payload = {
        "model_config": asdict(model_config),
        "loss_config": asdict(loss_config),
    }
    with config_path.open("w", encoding="utf-8") as f:
        json.dump(_to_jsonable(config_payload), f, ensure_ascii=False, indent=2)

    #训练过程统计
    stats_payload = {
        "train_stats": train_stats or {},
        "history": history or [],
        "extra_meta": extra_meta or {},
    }
    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(_to_jsonable(stats_payload), f, ensure_ascii=False, indent=2)

    return {
        "model_path": str(model_path),
        "config_path": str(config_path),
        "stats_path": str(stats_path),
    }


def load_training_artifacts(
    save_dir: str | Path,
    map_location: str = "cpu",
) -> Tuple[DualTowerTrainModel, DualTowerTrainConfig, LossConfig, Dict[str, Any]]:
    # 从磁盘加载训练产物并恢复模型到指定设备
    root = Path(save_dir)
    model_path = root / "model.pt"
    config_path = root / "config.json"
    stats_path = root / "stats.json"

    if not model_path.exists():
        raise FileNotFoundError(f"missing model file: {model_path}")
    if not config_path.exists():
        raise FileNotFoundError(f"missing config file: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        cfg = json.load(f)

    model_cfg_raw = cfg.get("model_config", {})
    loss_cfg_raw = cfg.get("loss_config", {})

    model_config = DualTowerTrainConfig(**model_cfg_raw)
    loss_config = LossConfig(**loss_cfg_raw)

    #推理时按指定设备加载并放置模型，避免线上设备配置与模型位置不一致。
    target_device = torch.device(str(map_location or "cpu"))

    model = DualTowerTrainModel(config=model_config).to(target_device)
    state = torch.load(model_path, map_location=target_device)
    model.load_state_dict(state)
    model.eval()

    stats: Dict[str, Any] = {}
    if stats_path.exists():
        with stats_path.open("r", encoding="utf-8") as f:
            stats = json.load(f)

    return model, model_config, loss_config, stats


class CachedArtifactLoader:
    # 线上推理用：进程内缓存，避免每次请求都重复加载模型

    # 初始化缓存状态
    def __init__(self) -> None:
        self._cache_key: Optional[str] = None
        self._cache_value: Optional[Tuple[DualTowerTrainModel, DualTowerTrainConfig, LossConfig, Dict[str, Any]]] = None

    # 获取缓存中的模型产物；必要时重新加载并更新缓存
    def get(
        self,
        save_dir: str | Path,
        map_location: str = "cpu",
        force_reload: bool = False,
    ) -> Tuple[DualTowerTrainModel, DualTowerTrainConfig, LossConfig, Dict[str, Any]]:
        key = f"{Path(save_dir).resolve()}::{map_location}"

        if (not force_reload) and self._cache_key == key and self._cache_value is not None:
            return self._cache_value

        loaded = load_training_artifacts(save_dir=save_dir, map_location=map_location)
        self._cache_key = key
        self._cache_value = loaded
        return loaded

    # 清空进程内缓存
    def clear(self) -> None:
        self._cache_key = None
        self._cache_value = None
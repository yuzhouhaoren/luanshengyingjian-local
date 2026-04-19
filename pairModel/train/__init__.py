"""Training and inference toolkit for the trainable dual-tower pipeline."""

from .artifacts import CachedArtifactLoader, load_training_artifacts, save_training_artifacts
from .data_split import split_train_val_pairs
from .dataset import PairDataset, collate_pair_batch
from .inference import trained_dual_tower_similarity
from .losses import LossConfig, compute_eval_loss, compute_train_loss
from .model_net import DualTowerTrainConfig, DualTowerTrainModel
from .trainer import TrainerConfig, fit_dual_tower

__all__ = [
    "CachedArtifactLoader",
    "load_training_artifacts",
    "save_training_artifacts",
    "split_train_val_pairs",
    "PairDataset",
    "collate_pair_batch",
    "trained_dual_tower_similarity",
    "LossConfig",
    "compute_eval_loss",
    "compute_train_loss",
    "DualTowerTrainConfig",
    "DualTowerTrainModel",
    "TrainerConfig",
    "fit_dual_tower",
]

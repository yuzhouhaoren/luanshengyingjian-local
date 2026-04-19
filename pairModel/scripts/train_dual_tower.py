from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple



PROJECT_ROOT = Path(__file__).resolve().parents[2]
PAIRMODEL_DIR = PROJECT_ROOT / "pairModel"
if str(PAIRMODEL_DIR) not in sys.path:
    sys.path.insert(0, str(PAIRMODEL_DIR))

from db.crud import build_labeled_pairs_from_db
from train.artifacts import save_training_artifacts
from train.data_split import split_train_val_pairs
from train.losses import LossConfig
from train.model_net import DualTowerTrainConfig
from train.trainer import TrainerConfig, fit_dual_tower


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the training entry script."""
    parser = argparse.ArgumentParser(description="Train dual-tower model from SQLite samples")

    parser.add_argument(
        "--intents",
        type=str,
        default="伴侣,朋友",
        help="Comma-separated intents. Supported: 伴侣,朋友",
    )
    parser.add_argument("--negative-ratio", type=float, default=1.0, help="Sampled negatives per positive")
    parser.add_argument("--val-ratio", type=float, default=0.2, help="Validation split ratio")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    parser.add_argument("--epochs", type=int, default=20, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Mini-batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--weight-decay", type=float, default=1e-5, help="Weight decay")
    parser.add_argument("--grad-clip", type=float, default=1.0, help="Gradient clipping norm")
    parser.add_argument("--patience", type=int, default=4, help="Early-stop patience")
    parser.add_argument("--device", type=str, default="cuda", help="cuda / cpu / mps")

    parser.add_argument("--hidden-dim", type=int, default=128, help="Tower hidden dimension")
    parser.add_argument("--output-dim", type=int, default=64, help="Tower output dimension")
    parser.add_argument("--dropout", type=float, default=0.1, help="Dropout ratio")

    parser.add_argument("--loss-main", type=float, default=1.0, help="Main loss weight")
    parser.add_argument("--loss-pref", type=float, default=0.2, help="Preference aux loss weight")
    parser.add_argument("--loss-intent", type=float, default=0.2, help="Intent aux loss weight")
    parser.add_argument("--loss-l2", type=float, default=0.0, help="L2 regularization weight")
    parser.add_argument("--label-smoothing", type=float, default=0.0, help="Label smoothing")
    parser.add_argument("--pos-weight", type=float, default=1.0, help="Positive class weight")

    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(PAIRMODEL_DIR / "artifacts" / "dual_tower"),
        help="Root directory to store trained artifacts",
    )

    return parser.parse_args()


def _normalize_intent_name(intent_text: str) -> str:
    """Normalize intent names to the two canonical business intents."""
    text = str(intent_text or "").strip()
    if text in {"伴侣", "intent_伴侣"}:
        return "伴侣"
    if text in {"朋友", "志趣相投的朋友", "intent_志趣相投的朋友"}:
        return "朋友"
    return ""


def _intent_subdir(intent_type: str) -> str:
    """Map intent to artifact subdirectory name."""
    return "partner" if intent_type == "伴侣" else "friend"


def _parse_intents(raw: str) -> List[str]:
    """Parse and deduplicate intent list while preserving supported values."""
    out: List[str] = []
    seen = set()
    for part in str(raw or "").split(","):
        name = _normalize_intent_name(part)
        if not name:
            continue
        if name in seen:
            continue
        seen.add(name)
        out.append(name)
    return out


def _count_labels(samples: Sequence[Dict[str, Any]]) -> Tuple[int, int]:
    """Count positive and negative labels for quick data-health checks."""
    pos = 0
    neg = 0
    for item in samples:
        try:
            label = float(item.get("label", 0.0))
        except (TypeError, ValueError):
            label = 0.0
        if label > 0.5:
            pos += 1
        else:
            neg += 1
    return pos, neg


def _infer_input_dims(samples: Sequence[Dict[str, Any]]) -> Tuple[int, int]:
    """Infer intent/profile input dimensions from sample vectors."""
    intent_dim = 0
    profile_dim = 0

    for item in samples:
        for key in ("seeker_intent_vector", "candidate_intent_vector"):
            vec = item.get(key)
            size = 0 if vec is None else int(getattr(vec, "size", len(vec) if hasattr(vec, "__len__") else 0))
            if size > intent_dim:
                intent_dim = size

        for key in ("seeker_profile_vector", "candidate_profile_vector"):
            vec = item.get(key)
            size = 0 if vec is None else int(getattr(vec, "size", len(vec) if hasattr(vec, "__len__") else 0))
            if size > profile_dim:
                profile_dim = size

    if intent_dim <= 0:
        raise ValueError("intent_dim inferred as 0, cannot train")

    if profile_dim < 0:
        profile_dim = 0

    return intent_dim, profile_dim


def _train_one_intent(intent_type: str, args: argparse.Namespace) -> Dict[str, Any]:
    """Train and save one intent-specific model and return run summary."""
    samples = build_labeled_pairs_from_db(
        intent_type=intent_type,
        negative_ratio=float(args.negative_ratio),
        random_seed=int(args.seed),
        include_rejected=True,
        only_pool_users=True,
    )

    if len(samples) < 10:
        raise RuntimeError(f"intent={intent_type} has too few samples: {len(samples)}")

    pos, neg = _count_labels(samples)
    if pos == 0 or neg == 0:
        raise RuntimeError(f"intent={intent_type} label distribution invalid: pos={pos}, neg={neg}")

    train_samples, val_samples, split_stats = split_train_val_pairs(
        samples=samples,
        val_ratio=float(args.val_ratio),
        random_seed=int(args.seed),
        group_by_seeker=True,
    )

    intent_dim, profile_dim = _infer_input_dims(samples)

    model_cfg = DualTowerTrainConfig(
        intent_input_dim=int(intent_dim),
        profile_input_dim=int(profile_dim),
        tower_hidden_dim=int(args.hidden_dim),
        tower_output_dim=int(args.output_dim),
        dropout=float(args.dropout),
        use_profile=int(profile_dim) > 0,
    )

    loss_cfg = LossConfig(
        main_weight=float(args.loss_main),
        preference_aux_weight=float(args.loss_pref),
        intent_aux_weight=float(args.loss_intent),
        l2_weight=float(args.loss_l2),
        label_smoothing=float(args.label_smoothing),
        positive_class_weight=float(args.pos_weight),
    )

    trainer_cfg = TrainerConfig(
        batch_size=int(args.batch_size),
        num_epochs=int(args.epochs),
        learning_rate=float(args.lr),
        weight_decay=float(args.weight_decay),
        grad_clip_norm=float(args.grad_clip),
        early_stop_patience=int(args.patience),
        device=str(args.device),
        seed=int(args.seed),
        log_every_steps=20,
    )

    result = fit_dual_tower(
        train_samples=train_samples,
        val_samples=val_samples,
        model_config=model_cfg,
        loss_config=loss_cfg,
        trainer_config=trainer_cfg,
    )

    save_dir = Path(args.output_dir) / _intent_subdir(intent_type)
    paths = save_training_artifacts(
        save_dir=save_dir,
        model=result["model"],
        model_config=model_cfg,
        loss_config=loss_cfg,
        train_stats={
            "intent_type": intent_type,
            "split": split_stats,
            "best_epoch": result["best_epoch"],
            "best_val_loss": result["best_val_loss"],
            "intent_dim": result["intent_dim"],
            "profile_dim": result["profile_dim"],
        },
        history=result["history"],
        extra_meta={
            "sample_count": len(samples),
            "pos_count": pos,
            "neg_count": neg,
        },
    )

    summary = {
        "intent_type": intent_type,
        "sample_count": len(samples),
        "pos_count": pos,
        "neg_count": neg,
        "train_size": len(train_samples),
        "val_size": len(val_samples),
        "best_epoch": result["best_epoch"],
        "best_val_loss": result["best_val_loss"],
        "save_dir": str(save_dir),
        "paths": paths,
    }
    return summary


def main() -> None:
    """Entry point: train one or both intent models and save artifacts."""
    args = _parse_args()
    intents = _parse_intents(args.intents)
    if not intents:
        raise SystemExit("No valid intents found. Use --intents 伴侣,朋友")

    print(f"[train] intents={intents}")
    print(f"[train] output_root={args.output_dir}")

    summaries: List[Dict[str, Any]] = []
    for intent_type in intents:
        print(f"\n[train] start intent={intent_type}")
        summary = _train_one_intent(intent_type=intent_type, args=args)
        summaries.append(summary)
        print(
            f"[train] done intent={intent_type} "
            f"best_epoch={summary['best_epoch']} best_val_loss={summary['best_val_loss']:.4f}"
        )
        print(f"[train] saved={summary['save_dir']}")

    print("\n[train] summary")
    for item in summaries:
        print(
            f"- intent={item['intent_type']} samples={item['sample_count']} "
            f"train={item['train_size']} val={item['val_size']} "
            f"best_val_loss={item['best_val_loss']:.4f}"
        )


if __name__ == "__main__":
    main()

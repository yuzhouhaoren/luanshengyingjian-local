from .llm_embedder import ReasonInput, TinyLLMReasoner, generate_match_reason

DualTowerConfig = None
DualTowerScorer = None

try:
	from .dual_tower_model import dual_tower_similarity
except Exception:
	try:
		from .dual_tower import DualTowerConfig, DualTowerScorer, dual_tower_similarity
	except Exception:
		dual_tower_similarity = None

__all__ = [
	"ReasonInput",
	"TinyLLMReasoner",
	"generate_match_reason",
	"DualTowerConfig",
	"DualTowerScorer",
	"dual_tower_similarity",
]

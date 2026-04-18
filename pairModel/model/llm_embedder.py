from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import numpy as np


#推荐理由生成输入结构
@dataclass(frozen=True)
class ReasonInput:
	seeker_name: str
	candidate_name: str
	intent_type: str
	match_score: float
	profile_similarity: Optional[float] = None


#轻量本地理由生成器，可在后续替换为真实 LLM 服务
class TinyLLMReasoner:
	"""A lightweight local reason generator for matching explanations.

	This module keeps zero external runtime dependency and can be replaced by
	a real LLM service in the future without changing caller code.
	"""

	#读取文案风格配置
	def __init__(self) -> None:
		self.style = os.getenv("PAIRMODEL_REASON_STYLE", "warm").strip().lower()

	#根据意向类型生成推荐理由
	def generate(self, payload: ReasonInput) -> str:
		candidate = payload.candidate_name or "对方"
		score = float(payload.match_score)
		score_text = f"{score * 100:.1f}%"
		profile_hint = self._profile_hint(payload.profile_similarity)

		if payload.intent_type == "伴侣":
			return self._partner_reason(candidate, score_text, profile_hint)
		return self._friend_reason(candidate, score_text, profile_hint)

	#伴侣意向理由模板
	def _partner_reason(self, candidate: str, score_text: str, profile_hint: str) -> str:
		if self.style == "concise":
			return f"你与{candidate}在伴侣维度匹配度为{score_text}，{profile_hint}。"

		return (
			f"你与{candidate}在伴侣关系关键维度上的契合度为{score_text}，"
			f"{profile_hint}，建议优先尝试深入交流。"
		)

	#朋友意向理由模板
	def _friend_reason(self, candidate: str, score_text: str, profile_hint: str) -> str:
		if self.style == "concise":
			return f"你与{candidate}在朋友维度匹配度为{score_text}，{profile_hint}。"

		return (
			f"你与{candidate}在朋友关系维度上的契合度为{score_text}，"
			f"{profile_hint}，适合从共同兴趣话题开始互动。"
		)

	@staticmethod
	#将画像相似度转为更易理解的解释文案
	def _profile_hint(profile_similarity: Optional[float]) -> str:
		if profile_similarity is None:
			return "你们在核心偏好上表现出较高一致性"

		value = float(profile_similarity)
		if value >= 0.85:
			return "人格与相处节奏高度协调"
		if value >= 0.65:
			return "人格和沟通方式较为互补"
		if value >= 0.45:
			return "基础画像上存在可发展交集"
		return "你们存在差异但仍有可探索空间"


#安全余弦相似度，避免空向量和维度不匹配导致异常
def cosine_similarity_safe(vector_a: np.ndarray, vector_b: np.ndarray) -> Optional[float]:
	if vector_a.size == 0 or vector_b.size == 0:
		return None
	if int(vector_a.shape[0]) != int(vector_b.shape[0]):
		return None

	denominator = float(np.linalg.norm(vector_a) * np.linalg.norm(vector_b))
	if denominator <= 1e-8:
		return None
	score = float(np.dot(vector_a, vector_b) / denominator)
	return max(-1.0, min(1.0, score))


#模块级单例，避免重复初始化
_REASONER = TinyLLMReasoner()


#统一理由生成入口，业务层只调用这个函数
def generate_match_reason(
	seeker_name: str,
	candidate_name: str,
	intent_type: str,
	match_score: float,
	seeker_profile_vector: Optional[np.ndarray] = None,
	candidate_profile_vector: Optional[np.ndarray] = None,
) -> str:
	profile_similarity: Optional[float] = None
	if seeker_profile_vector is not None and candidate_profile_vector is not None:
		profile_similarity = cosine_similarity_safe(seeker_profile_vector, candidate_profile_vector)

	payload = ReasonInput(
		seeker_name=seeker_name,
		candidate_name=candidate_name,
		intent_type=intent_type,
		match_score=match_score,
		profile_similarity=profile_similarity,
	)
	return _REASONER.generate(payload)

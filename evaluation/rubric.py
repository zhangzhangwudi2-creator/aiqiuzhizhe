"""Deterministic quality checks for saved model outputs.

The evaluator intentionally avoids calling an LLM. Human-written expectations define
what a useful answer should cover, while Pydantic still validates the response shape.
"""

from dataclasses import dataclass
from typing import Any

from schemas import AnalysisResult


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    contract_valid: bool
    keyword_hits: int
    keyword_total: int
    forbidden_hits: tuple[str, ...]
    score_in_range: bool

    @property
    def keyword_recall(self) -> float:
        if not self.keyword_total:
            return 1.0
        return self.keyword_hits / self.keyword_total

    @property
    def passed(self) -> bool:
        return (
            self.contract_valid
            and self.keyword_recall >= 0.75
            and not self.forbidden_hits
            and self.score_in_range
        )


def evaluate_case(case: dict[str, Any]) -> CaseResult:
    """Evaluate one saved output against human-written expectations."""
    case_id = case.get("case_id", "unknown")
    output = case.get("output", {})
    expectations = case.get("expectations", {})

    try:
        result = AnalysisResult.model_validate(output)
        contract_valid = True
    except Exception:
        result = None
        contract_valid = False

    searchable = str(output).lower()
    required = [str(term).lower() for term in expectations.get("required_terms", [])]
    forbidden = [str(term).lower() for term in expectations.get("forbidden_terms", [])]
    hits = sum(term in searchable for term in required)
    forbidden_hits = tuple(term for term in forbidden if term in searchable)

    score_range = expectations.get("score_range", [0, 100])
    score_in_range = bool(
        result
        and len(score_range) == 2
        and score_range[0] <= result.overall_score <= score_range[1]
    )

    return CaseResult(
        case_id=case_id,
        contract_valid=contract_valid,
        keyword_hits=hits,
        keyword_total=len(required),
        forbidden_hits=forbidden_hits,
        score_in_range=score_in_range,
    )

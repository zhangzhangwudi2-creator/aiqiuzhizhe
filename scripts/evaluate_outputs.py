"""Offline contract evaluation that does not call an AI API."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.rubric import evaluate_case  # noqa: E402


def main() -> int:
    cases_path = ROOT / "evaluation" / "sample_outputs.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    results = [evaluate_case(case) for case in cases]
    passed = sum(result.passed for result in results)
    total_keywords = sum(result.keyword_total for result in results)
    total_hits = sum(result.keyword_hits for result in results)
    recall = total_hits / total_keywords if total_keywords else 1.0

    print(f"Quality evaluation: {passed}/{len(results)} cases passed")
    print(f"Required-term recall: {recall:.0%} ({total_hits}/{total_keywords})")
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(
            f"- {status} {result.case_id}: contract={result.contract_valid}, "
            f"terms={result.keyword_hits}/{result.keyword_total}, "
            f"score_range={result.score_in_range}, "
            f"forbidden={list(result.forbidden_hits)}"
        )
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Offline contract evaluation that does not call an AI API."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from schemas import AnalysisResult  # noqa: E402


def main() -> int:
    cases_path = ROOT / "evaluation" / "sample_outputs.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    failures: list[str] = []

    for case in cases:
        try:
            AnalysisResult.model_validate(case["output"])
        except Exception as exc:
            failures.append(f"{case.get('case_id', 'unknown')}: {exc}")

    passed = len(cases) - len(failures)
    print(f"Contract evaluation: {passed}/{len(cases)} passed")
    for failure in failures:
        print(f"- {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

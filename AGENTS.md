# Codex collaboration guide

## User goal

The repository owner is a data-science undergraduate preparing for an AI application,
AI operations, or AI product internship. Code changes should improve both the project
and the owner's ability to explain the work in an interview.

## Working style

- Use plain Chinese when teaching or reporting results.
- Assume beginner-level Python knowledge. Explain the business reason before syntax.
- During teaching, give one small exercise at a time instead of a complete solution.
- For implementation tasks, Codex may write the code, but must identify the 1-3 ideas
  the owner should understand and add or update interview notes when the change is
  resume-relevant.
- Do not invent users, accuracy, conversion rates, awards, or performance improvements.
- Clearly separate measured results from plans and estimates.

## Project boundaries

- The deployed application is the root `main.py` plus `static/`, not the unfinished
  experimental `backend/` and `frontend/` directories.
- Do not call a paid AI API during tests unless the user explicitly requests it.
- Never commit `.env`, API keys, personal resumes, phone numbers, or raw recruiting
  conversations.
- Preserve the privacy claim: uploaded PDFs are processed in memory and not persisted.

## Environment and verification

- Use the repository-local 64-bit interpreter: `.venv/Scripts/python.exe` on Windows.
- Install development dependencies with:
  `.venv/Scripts/python.exe -m pip install -r requirements-dev.txt`
- Run before committing Python changes:
  - `.venv/Scripts/python.exe -m pytest -q`
  - `.venv/Scripts/python.exe scripts/evaluate_outputs.py`
  - `.venv/Scripts/python.exe -m compileall -q main.py prompts.py schemas.py quota.py evaluation scripts tests`
- Keep README claims synchronized with actual test and evaluation results.

## Priority order

1. Reliability, privacy, evaluation, and explainability.
2. A small set of real, anonymized evaluation cases.
3. Prompt-version comparison with reproducible evidence.
4. GitHub presentation and interview explanation.
5. New features only when they support a real user problem.


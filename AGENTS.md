# AGENTS.md

AI internship project preparation toolkit. Turns a JD into a resume-ready and interview-ready project.

## Setup

```bash
cd shushu-internship-tool
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

Requires Python >=3.10. Dev deps: pytest>=8, PyYAML>=6.

## Test

```bash
pytest
```

No lint, typecheck, or formatter is configured. Do not assume ruff/mypy/black exist.

## Source Layout

Package source is **not** at repo root. It lives at:

```
skills/shushu-internship-tool/scripts/shushu_internship_tool/
```

- `repo_audit.py` — scan a repo, generate `audit.json` / `overview.md` / `overview.html`
- `candidate_score.py` — rank candidate projects by JD match + taste
- `interview_pack.py` — generate interview material skeleton
- `common.py` — shared utilities

Entry points (after install): `shushu-repo-audit`, `shushu-candidate-score`, `shushu-interview-pack`.

## Tests

Tests live in `tests/`. The fixture repo `tests/fixtures/tiny_ai_project/` is used by `test_repo_audit.py` — avoid modifying it casually.

`test_skill_instructions.py` validates structural invariants in `SKILL.md` and `openai.yaml` — editing those files can break tests.

## Key Gotchas

- `pyproject.toml` sets `pythonpath = ["skills/shushu-internship-tool/scripts"]` and `testpaths = ["tests"]`. Source import path is `shushu_internship_tool.*`, not a top-level package.
- `candidate_score.py` does **not** parse natural-language preferences. The AI agent must write structured fields (`matched_jd_terms`, `license_score`, `runnable_score`, `resource_fit_score`) and pass `--taste taste.json` with `prefer_tags`/`avoid_tags`.
- The skill workflow (in `SKILL.md`) requires structured user-input controls (yes/no gate, A/B/C/D options) — do not simulate these as plain text.
- No CI, no pre-commit hooks, no GitHub Actions.

## Out of Scope

`data_agent_project/` is a separate sub-project (data analysis agent). Do not treat it as part of this skill.

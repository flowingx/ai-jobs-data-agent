from __future__ import annotations

import argparse
import math
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .common import ensure_dir, load_json, markdown_table, normalize_list, safe_int, write_json, write_text


PERMISSIVE_LICENSE_HINTS = {
    "mit",
    "apache",
    "apache-2.0",
    "bsd",
    "mpl",
    "isc",
}

def tokenize(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_+.#-]{1,}", text)}


def parse_candidates(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [dict(item) for item in value]
    if isinstance(value, dict) and isinstance(value.get("candidates"), list):
        return [dict(item) for item in value["candidates"]]
    raise ValueError("candidates JSON must be a list or an object with a 'candidates' list")


def parse_commit_date(raw: Any) -> date | None:
    if not raw:
        return None
    text = str(raw).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y"):
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.date()
        except ValueError:
            continue
    return None


def license_score(raw: Any) -> tuple[int, str]:
    text = str(raw or "").strip().lower()
    if not text or text in {"unknown", "none", "n/a"}:
        return 0, "license unknown, note source before publishing"
    if any(hint in text for hint in PERMISSIVE_LICENSE_HINTS):
        return 4, "license is easy to work with"
    if "gpl" in text or "agpl" in text:
        return 1, "copyleft license, check before publishing derived code"
    return 2, "license present"


def runnable_score(raw: Any) -> tuple[int, str]:
    if isinstance(raw, bool):
        return (20, "runnable") if raw else (-5, "not verified runnable")
    text = str(raw or "").strip().lower()
    if text in {"true", "yes", "y", "runnable", "ok", "verified"}:
        return 20, "runnable"
    if text in {"partial", "maybe", "unknown", "readme-only", "needs_fix"}:
        return 10, "partially runnable or needs verification"
    if text in {"false", "no", "n", "broken"}:
        return -5, "not verified runnable"
    return 5, "runnable status unclear"


def compute_score(raw: Any) -> tuple[int, str]:
    text = str(raw or "").strip().lower().replace("-", "_").replace(" ", "_")
    if not text or text in {"unknown", "n/a"}:
        return 5, "run resources unknown"
    if any(key in text for key in ("cpu", "local", "docker", "compose", "sqlite", "free", "small", "laptop")):
        return 10, "local or low-resource run"
    if any(key in text for key in ("cloud", "vps", "server", "postgres", "mysql", "redis", "mongodb", "supabase", "vercel", "railway")):
        return 8, "light cloud or managed service feasible"
    if any(key in text for key in ("colab", "single_gpu", "1gpu", "one_gpu", "t4", "4090", "a10", "a100")):
        return 8, "single GPU or notebook feasible"
    if any(key in text for key in ("multi_gpu", "distributed", "cluster", "large", "expensive", "multi_region")):
        return 3, "high resource risk"
    return 6, "run resources likely manageable"


def activity_score(raw: Any, today: date) -> tuple[int, str]:
    commit_date = parse_commit_date(raw)
    if commit_date is None:
        return 0, "last_commit missing or unparsable"
    days = max((today - commit_date).days, 0)
    if days <= 180:
        return 10, "active within 180 days"
    if days <= 365:
        return 7, "active within 1 year"
    if days <= 730:
        return 4, "active within 2 years"
    return 1, "inactive for more than 2 years"


def stars_score(raw: Any) -> tuple[int, str]:
    stars = safe_int(raw)
    if stars >= 1000:
        return 10, "strong community signal"
    if stars >= 200:
        return 8, "good community signal"
    if stars >= 50:
        return 6, "some community signal"
    if stars > 0:
        return 3, "small community signal"
    return 0, "no star signal"


def keyword_score(candidate: dict[str, Any], jd_text: str) -> tuple[int, list[str], str]:
    jd_tokens = tokenize(jd_text)
    keywords = normalize_list(candidate.get("jd_keywords"))
    tags = normalize_list(candidate.get("tags"))
    agent_matches = normalize_list(candidate.get("matched_jd_terms"))
    explicit_matches = list(agent_matches)
    for keyword in keywords:
        keyword_lower = keyword.lower()
        keyword_tokens = tokenize(keyword)
        if (
            not keyword_tokens
            or keyword_lower in jd_text.lower()
            or keyword_tokens & jd_tokens
        ):
            explicit_matches.append(keyword)
    tag_matches = []
    for tag in tags:
        tag_lower = tag.lower()
        if tokenize(tag) & jd_tokens or tag_lower in jd_text.lower():
            tag_matches.append(tag)
    matched = list(dict.fromkeys([*explicit_matches, *tag_matches]))
    score = min(30, len(matched) * 5)
    reason = f"{len(matched)} JD/tag matches"
    return score, matched, reason


def score_candidate(candidate: dict[str, Any], jd_text: str, today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    keyword_points, matched_keywords, keyword_reason = keyword_score(candidate, jd_text)
    license_points, license_reason = license_score(candidate.get("license"))
    runnable_points, runnable_reason = runnable_score(candidate.get("runnable"))
    compute_points, compute_reason = compute_score(candidate.get("compute", candidate.get("resources")))
    activity_points, activity_reason = activity_score(candidate.get("last_commit"), today)
    stars_points, stars_reason = stars_score(candidate.get("stars"))

    mod_ideas = normalize_list(candidate.get("mod_ideas"))
    mod_points = min(20, len(mod_ideas) * 5)
    risk_notes = normalize_list(candidate.get("risk_notes"))
    risk_penalty = min(20, len(risk_notes) * 3)

    raw_score = (
        keyword_points
        + license_points
        + runnable_points
        + compute_points
        + activity_points
        + stars_points
        + mod_points
        - risk_penalty
    )
    score = max(0, min(100, int(math.ceil(raw_score))))

    return {
        **candidate,
        "score": score,
        "score_breakdown": {
            "jd_match": keyword_points,
            "license": license_points,
            "runnable": runnable_points,
            "resource_fit": compute_points,
            "activity": activity_points,
            "stars": stars_points,
            "modification_space": mod_points,
            "risk_penalty": -risk_penalty,
        },
        "matched_keywords": matched_keywords,
        "score_reasons": [
            keyword_reason,
            license_reason,
            runnable_reason,
            compute_reason,
            activity_reason,
            stars_reason,
            f"{len(mod_ideas)} modification ideas",
            f"{len(risk_notes)} risk notes",
        ],
    }


def rank_candidates(jd_text: str, candidates: list[dict[str, Any]], today: date | None = None) -> list[dict[str, Any]]:
    scored = [score_candidate(candidate, jd_text, today=today) for candidate in candidates]
    return sorted(scored, key=lambda item: (-safe_int(item.get("score")), str(item.get("name", "")).lower()))


def render_markdown(ranked: list[dict[str, Any]], jd_path: str | None = None) -> str:
    rows = []
    for index, item in enumerate(ranked, start=1):
        rows.append(
            [
                index,
                item.get("name", "unnamed"),
                item.get("score", 0),
                item.get("license", ""),
                item.get("stars", ""),
                item.get("last_commit", ""),
                item.get("runnable", ""),
                item.get("compute", item.get("resources", "")),
                ", ".join(normalize_list(item.get("matched_keywords"))[:6]),
                "; ".join(normalize_list(item.get("risk_notes"))[:3]) or "无",
            ]
        )

    best = ranked[0] if ranked else None
    backup = ranked[1] if len(ranked) > 1 else None
    parts = [
        "# 候选项目排序",
        "",
        f"- JD 来源：`{jd_path}`" if jd_path else "- JD 来源：未记录",
        f"- 主项目推荐：`{best.get('name')}`，score={best.get('score')}" if best else "- 主项目推荐：TODO",
        f"- 备选项目：`{backup.get('name')}`，score={backup.get('score')}" if backup else "- 备选项目：TODO",
        "",
        markdown_table(
            ["Rank", "Name", "Score", "License", "Stars", "Last Commit", "Runnable", "Resources", "Matched", "Risks"],
            rows,
        ),
        "",
        "## 使用说明",
        "",
        "- 这个脚本只根据显式字段打分；语义判断、JD 命中度和最终选择仍需 AI 助手/人工审阅。",
        "- 不可运行、资源要求过高、风险说明过多的项目，除非非常贴 JD，否则不建议作为主项目。",
        "- 推荐项目应尽快进入最小路径摸底、简历 4-5 行版本和面试 Q&A，而不是卡在完美复现。",
    ]
    return "\n".join(parts)


def write_ranking_outputs(ranked: list[dict[str, Any]], out_dir: str | Path, jd_path: str | None = None) -> dict[str, str]:
    out = ensure_dir(out_dir)
    paths = {
        "candidate_score_json": str(write_json(out / "candidate_score.json", {"candidates": ranked})),
        "candidate_score_md": str(write_text(out / "candidate_score.md", render_markdown(ranked, jd_path=jd_path))),
    }
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rank GitHub project candidates for a computer-industry internship JD.")
    parser.add_argument("--jd", required=True, help="Path to a text file containing the target job description.")
    parser.add_argument("--candidates", required=True, help="Path to candidate JSON.")
    parser.add_argument("--out", required=True, help="Output directory.")
    args = parser.parse_args(argv)

    jd_path = Path(args.jd)
    jd_text = jd_path.read_text(encoding="utf-8", errors="replace")
    candidates = parse_candidates(load_json(args.candidates))
    ranked = rank_candidates(jd_text, candidates)
    paths = write_ranking_outputs(ranked, args.out, jd_path=str(jd_path))
    for label, path in paths.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

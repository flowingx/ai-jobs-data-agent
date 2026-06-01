from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from .common import (
    ensure_dir,
    load_json,
    markdown_table,
    normalize_list,
    safe_float,
    safe_int,
    write_json,
    write_text,
)


PERMISSIVE_LICENSE_HINTS = {
    "mit",
    "apache",
    "apache-2.0",
    "bsd",
    "mpl",
    "isc",
}

NO_TASTE_MAX_RAW_SCORE = 104
TASTE_MAX_RAW_SCORE = 114
USER_PREFERENCE_MAX_SCORE = 10

# Exact / near-exact no-op texts for the optional --taste text file compatibility path.
# The interactive skill gate uses explicit yes/no instead of this list.
NOOP_TASTE_TEXTS = {
    "",
    "无",
    "没有",
    "暂无",
    "无偏好",
    "没有偏好",
    "没偏好",
    "都可以",
    "都行",
    "随便",
    "跳过",
    "略过",
    "不用",
    "按jd推荐",
    "按默认推荐",
    "无按jd推荐",
    "无按岗位推荐",
    "无按默认推荐",
    "没有按jd推荐",
    "none",
    "na",
    "n/a",
    "no",
    "nopreference",
    "nopreferences",
    "no-preference",
    "no-preferences",
    "skip",
}

# A deliberately small alias table. It is not a full semantic model; the agent should
# still normalize rich taste into prefer_tags / avoid_tags whenever possible.
TAG_ALIASES: dict[str, tuple[str, ...]] = {
    "backend": ("backend", "back-end", "后端", "服务端", "server-side", "server side", "fastapi", "spring", "django", "flask"),
    "frontend": ("frontend", "front-end", "前端", "react", "vue", "页面", "ui", "web ui"),
    "pure-frontend": ("pure-frontend", "pure frontend", "纯前端", "only frontend", "frontend-only", "前端only", "只有前端"),
    "fullstack": ("fullstack", "full-stack", "全栈", "前后端", "端到端"),
    "mobile": ("mobile", "移动端", "android", "ios", "flutter", "react native"),
    "ai-app": ("ai", "ai-app", "ai app", "ai应用", "ai 应用", "人工智能", "人工智能应用", "大模型应用", "llm application", "llm app", "rag应用", "智能应用"),
    "rag": ("rag", "检索增强", "向量检索", "retrieval augmented", "retrieval-augmented"),
    "llm": ("llm", "大模型", "语言模型", "large language model", "openai", "chatglm", "qwen"),
    "recommendation": ("recommendation", "recommender", "推荐系统", "推荐算法", "排序", "ranking", "召回"),
    "data-engineering": ("data-engineering", "data engineering", "数据工程", "etl", "airflow", "spark", "数据仓库", "数仓", "pipeline"),
    "devops": ("devops", "cloud-native", "cloud native", "云原生", "kubernetes", "k8s", "ci/cd", "cicd", "部署"),
    "infra": ("infra", "infrastructure", "基础架构", "系统", "分布式", "存储", "网络"),
    "security": ("security", "安全", "鉴权", "认证", "漏洞", "审计"),
    "testing": ("testing", "测试", "test", "单测", "集成测试", "e2e", "pytest", "unittest"),
    "local-docker": ("local-docker", "local docker", "docker", "docker compose", "docker-compose", "本地docker", "本地 docker", "本地跑通", "本地运行", "本地能跑", "本机跑通", "本机运行"),
    "interview-friendly": ("interview-friendly", "interview friendly", "适合面试", "适合面试讲", "面试友好", "能讲清", "可讲", "简历好讲", "面试讲"),
    "engineering-depth": ("engineering-depth", "engineering depth", "工程深度", "工程链路", "技术深度", "系统设计", "架构设计"),
    "api": ("api", "rest-api", "rest api", "接口", "接口设计", "endpoint", "http"),
    "database": ("database", "db", "数据库", "mysql", "postgresql", "postgres", "sqlite", "mongodb", "schema"),
    "cache": ("cache", "缓存", "redis", "memcached"),
    "queue": ("queue", "消息队列", "mq", "kafka", "rabbitmq", "celery", "异步任务"),
    "ci-cd": ("ci-cd", "ci/cd", "cicd", "github actions", "gitlab ci", "持续集成", "持续部署"),
    "deployment": ("deployment", "deploy", "部署", "上线", "发布", "运维"),
    "single-gpu": ("single-gpu", "single gpu", "one gpu", "1gpu", "单卡", "t4", "4090", "a10", "colab"),
    "multi-gpu": ("multi-gpu", "multi gpu", "multi-gpu", "多机多卡", "多卡", "分布式训练", "gpu cluster", "重gpu", "重 gpu"),
    "cloud-heavy": ("cloud-heavy", "cloud heavy", "复杂云", "复杂云服务", "重云服务", "云账号", "cloud account", "aws", "gcp", "azure"),
    "cloud-only": ("cloud-only", "cloud only", "只能上云", "必须上云", "云端限定"),
    "large-dataset": ("large-dataset", "large dataset", "大数据集", "海量数据", "私有数据", "private dataset"),
    "too-heavy": ("too-heavy", "too heavy", "太重", "环境太重", "依赖太重", "heavy environment"),
}

NEGATION_CUES = (
    "不想",
    "不要",
    "避免",
    "不希望",
    "不愿",
    "别",
    "不碰",
    "不依赖",
    "不需要",
    "拒绝",
    "远离",
    "不做",
    "没有",
    "没法",
    "无法",
    "no ",
    "not ",
    "avoid",
    "without",
    "don't",
    "dont",
    "do not",
)

EXPLICIT_PREFER_KEYS = ("prefer_tags", "preferred_tags", "preference_tags", "taste_tags")
EXPLICIT_AVOID_KEYS = ("avoid_tags", "negative_tags", "mismatch_tags")


def tokenize(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_+.#-]{1,}", text)}


def parse_candidates(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [dict(item) for item in value]
    if isinstance(value, dict) and isinstance(value.get("candidates"), list):
        return [dict(item) for item in value["candidates"]]
    raise ValueError("candidates JSON must be a list or an object with a 'candidates' list")


def _compact_taste_text(text: str) -> str:
    normalized = text.strip().lower()
    normalized = normalized.replace("job description", "jd")
    normalized = normalized.replace("岗位描述", "jd").replace("职位描述", "jd")
    for label in (
        "project preference",
        "personal preference",
        "preference",
        "taste",
        "项目偏好",
        "用户偏好",
        "个人偏好",
        "偏好",
    ):
        normalized = normalized.replace(label, "")
    return re.sub(r"[\s`'\"。，、；;：:,/\\|!！?？（）()\[\]{}<>《》_-]+", "", normalized)


def has_effective_taste(taste_text: str | None) -> bool:
    """Return whether an optional --taste text file contains a concrete preference.

    This intentionally uses exact / near-exact no-op text matching only for CLI file
    compatibility. The conversational gate should remain explicit yes/no.
    """
    if taste_text is None:
        return False
    if not taste_text.strip():
        return False
    noop_compacts = {_compact_taste_text(text) for text in NOOP_TASTE_TEXTS}
    compact = _compact_taste_text(taste_text)
    if compact in noop_compacts:
        return False

    # Treat combinations such as "无 / 都可以" or "none, skip" as no-op too,
    # while keeping mixed input like "无，但其实更偏后端" effective.
    raw_segments = re.split(
        r"[\s`\'\"。，、；;：:,/\\|!！?？（）()\[\]{}<>《》_-]+",
        taste_text.strip(),
    )
    segments = [_compact_taste_text(segment) for segment in raw_segments if _compact_taste_text(segment)]
    if segments and all(segment in noop_compacts for segment in segments):
        return False
    return True


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


def _tag_slug(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("_", "-").replace("+", "-")
    text = re.sub(r"[\s/]+", "-", text)
    text = re.sub(r"[^a-z0-9.#\-一-鿿]+", "", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def _english_like(text: str) -> bool:
    return bool(text) and all(ord(ch) < 128 for ch in text)


def _alias_positions(text: str, alias: str) -> list[int]:
    if not alias:
        return []
    text_lower = text.lower()
    alias_lower = alias.lower()
    if _english_like(alias_lower):
        pattern = re.compile(rf"(?<![a-z0-9]){re.escape(alias_lower)}(?![a-z0-9])")
        return [match.start() for match in pattern.finditer(text_lower)]
    positions: list[int] = []
    start = 0
    while True:
        index = text_lower.find(alias_lower, start)
        if index == -1:
            break
        positions.append(index)
        start = index + len(alias_lower)
    return positions


def _has_alias(text: str, alias: str) -> bool:
    return bool(_alias_positions(text, alias))


def _canonicalize_one(value: str) -> set[str]:
    tags = {_tag_slug(value)} if _tag_slug(value) else set()
    for canonical, aliases in TAG_ALIASES.items():
        if _tag_slug(value) == _tag_slug(canonical) or any(
            _has_alias(value, alias) or _tag_slug(value) == _tag_slug(alias)
            for alias in aliases
        ):
            tags.add(canonical)
    if "cloud-only" in tags:
        tags.add("cloud-heavy")
    return tags


def canonicalize_tags(values: Any) -> set[str]:
    tags: set[str] = set()
    for value in normalize_list(values):
        tags.update(_canonicalize_one(value))
    return {tag for tag in tags if tag}


def _parse_json_taste(text: str) -> tuple[set[str], set[str]]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return set(), set()
    if not isinstance(data, dict):
        return set(), set()
    prefer: set[str] = set()
    avoid: set[str] = set()
    for key in EXPLICIT_PREFER_KEYS:
        prefer.update(canonicalize_tags(data.get(key)))
    for key in EXPLICIT_AVOID_KEYS:
        avoid.update(canonicalize_tags(data.get(key)))
    return prefer, avoid


def _parse_explicit_tag_lines(text: str) -> tuple[set[str], set[str], str]:
    prefer: set[str] = set()
    avoid: set[str] = set()
    consumed_patterns = [*EXPLICIT_PREFER_KEYS, *EXPLICIT_AVOID_KEYS]
    line_pattern = re.compile(
        rf"(?im)^\s*({'|'.join(re.escape(key) for key in consumed_patterns)})\s*[:=]\s*(.+)$"
    )
    for match in line_pattern.finditer(text):
        key = match.group(1).lower()
        raw_values = match.group(2).strip().strip("[]{}()")
        values = normalize_list(raw_values.replace('"', "").replace("'", ""))
        if key in EXPLICIT_AVOID_KEYS:
            avoid.update(canonicalize_tags(values))
        else:
            prefer.update(canonicalize_tags(values))
    free_text = line_pattern.sub("", text)
    return prefer, avoid, free_text


def _negative_context(text: str, start: int) -> bool:
    window = text[max(0, start - 18): start].lower()
    return any(cue in window for cue in NEGATION_CUES)


def _is_part_of_pure_frontend_phrase(text: str, start: int, alias: str) -> bool:
    window = text[max(0, start - 12): start + len(alias) + 12].lower()
    return any(
        phrase in window
        for phrase in ("纯前端", "pure frontend", "only frontend", "frontend-only", "只有前端")
    )


def _add_gpu_resource_avoidance(text: str, avoid: set[str]) -> None:
    lowered = text.lower()
    if re.search(
        r"(无|没有|没|不要|不想|不希望|避免|不依赖|without|no|not).{0,8}(gpu|显卡)",
        lowered,
    ):
        avoid.add("multi-gpu")
    if re.search(r"(多机多卡|多卡|重\s*gpu|multi[-\s]?gpu|gpu\s*cluster)", lowered) and any(
        cue in lowered for cue in NEGATION_CUES
    ):
        avoid.add("multi-gpu")


def parse_user_taste(taste_text: str | None) -> tuple[set[str], set[str]]:
    """Lightly normalize natural-language taste into prefer_tags and avoid_tags.

    The parser supports common Chinese substrings and English aliases. It is meant as
    a small scoring helper, not as a replacement for agent-side semantic analysis.
    """
    if not has_effective_taste(taste_text):
        return set(), set()

    assert taste_text is not None
    prefer, avoid = _parse_json_taste(taste_text)
    explicit_prefer, explicit_avoid, free_text = _parse_explicit_tag_lines(taste_text)
    prefer.update(explicit_prefer)
    avoid.update(explicit_avoid)

    for canonical, aliases in TAG_ALIASES.items():
        for alias in aliases:
            for start in _alias_positions(free_text, alias):
                if canonical == "frontend" and _is_part_of_pure_frontend_phrase(free_text, start, alias):
                    continue
                if _negative_context(free_text, start):
                    avoid.add(canonical)
                else:
                    prefer.add(canonical)

    _add_gpu_resource_avoidance(free_text, avoid)

    # Avoid tags are stronger than positive matches for the same canonical concept.
    prefer.difference_update(avoid)
    return prefer, avoid


def _ordered_intersection(items: Iterable[str], wanted: set[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item in wanted and item not in result:
            result.append(item)
    return result


def taste_score(candidate: dict[str, Any], taste_text: str | None) -> tuple[int, list[str], list[str], list[str]]:
    if not has_effective_taste(taste_text):
        return 0, [], [], []

    prefer_tags, user_avoid_tags = parse_user_taste(taste_text)
    positive_tags = canonicalize_tags([
        *normalize_list(candidate.get("taste_tags")),
        *normalize_list(candidate.get("tags")),
    ])
    project_avoid_tags = canonicalize_tags(candidate.get("avoid_tags"))

    matches = _ordered_intersection(sorted(positive_tags), prefer_tags)
    mismatches = _ordered_intersection(sorted(project_avoid_tags), user_avoid_tags)

    points = min(USER_PREFERENCE_MAX_SCORE, len(matches) * 2) - min(4, len(mismatches) * 2)
    points = max(0, points)

    notes: list[str] = []
    if matches:
        notes.append("匹配用户偏好：" + ", ".join(matches[:8]))
    else:
        notes.append("未命中显式用户偏好标签")
    if mismatches:
        notes.append("命中用户避雷项：" + ", ".join(mismatches[:8]))
    notes.append(f"user_preference={points}/{USER_PREFERENCE_MAX_SCORE}")
    return points, matches, mismatches, notes


def normalize_score(raw_score: float, max_raw_score: float) -> float:
    if max_raw_score <= 0:
        return 0.0
    x = max(0.0, min(float(raw_score), float(max_raw_score)))
    return round(x * 100 / float(max_raw_score), 2)


def score_candidate(
    candidate: dict[str, Any],
    jd_text: str,
    today: date | None = None,
    taste_text: str | None = None,
) -> dict[str, Any]:
    today = today or date.today()
    effective_taste = has_effective_taste(taste_text)
    max_raw_score = TASTE_MAX_RAW_SCORE if effective_taste else NO_TASTE_MAX_RAW_SCORE

    keyword_points, matched_keywords, keyword_reason = keyword_score(candidate, jd_text)
    license_points, license_reason = license_score(candidate.get("license"))
    runnable_points, runnable_reason = runnable_score(candidate.get("runnable"))
    compute_points, compute_reason = compute_score(candidate.get("compute", candidate.get("resources")))
    activity_points, activity_reason = activity_score(candidate.get("last_commit"), today)
    stars_points, stars_reason = stars_score(candidate.get("stars"))
    user_preference_points, taste_matches, taste_mismatches, preference_notes = taste_score(candidate, taste_text)

    mod_ideas = normalize_list(candidate.get("mod_ideas"))
    mod_points = min(20, len(mod_ideas) * 5)
    risk_notes = normalize_list(candidate.get("risk_notes"))
    risk_penalty_points = min(20, len(risk_notes) * 3)

    raw_score = (
        keyword_points
        + license_points
        + runnable_points
        + compute_points
        + activity_points
        + stars_points
        + mod_points
        + user_preference_points
        - risk_penalty_points
    )
    score = normalize_score(raw_score, max_raw_score)

    score_reasons = [
        keyword_reason,
        license_reason,
        runnable_reason,
        compute_reason,
        activity_reason,
        stars_reason,
        f"{len(mod_ideas)} modification ideas",
        f"{len(risk_notes)} risk notes",
    ]
    if effective_taste:
        score_reasons.append(
            f"user preference {user_preference_points}/{USER_PREFERENCE_MAX_SCORE}: "
            f"{len(taste_matches)} matches, {len(taste_mismatches)} avoid matches"
        )

    result: dict[str, Any] = {
        **candidate,
        "score": score,
        "raw_score": raw_score,
        "max_raw_score": max_raw_score,
        "score_breakdown": {
            "jd_match": keyword_points,
            "license": license_points,
            "runnable": runnable_points,
            "resource_fit": compute_points,
            "activity": activity_points,
            "stars": stars_points,
            "modification_space": mod_points,
            "user_preference": user_preference_points,
            "risk_penalty": -risk_penalty_points,
        },
        "matched_keywords": matched_keywords,
        "score_reasons": score_reasons,
    }
    if effective_taste:
        result.update(
            {
                "taste_matches": taste_matches,
                "taste_mismatches": taste_mismatches,
                "user_preference_notes": preference_notes,
            }
        )
    return result


def rank_candidates(
    jd_text: str,
    candidates: list[dict[str, Any]],
    today: date | None = None,
    taste_text: str | None = None,
) -> list[dict[str, Any]]:
    scored = [
        score_candidate(candidate, jd_text, today=today, taste_text=taste_text)
        for candidate in candidates
    ]
    return sorted(
        scored,
        key=lambda item: (-safe_float(item.get("score")), str(item.get("name", "")).lower()),
    )


def _format_score(value: Any) -> str:
    return f"{safe_float(value):.2f}"


def _should_include_taste_column(ranked: list[dict[str, Any]], include_taste: bool | None) -> bool:
    if include_taste is not None:
        return include_taste
    return any(safe_int(item.get("max_raw_score")) == TASTE_MAX_RAW_SCORE for item in ranked)


def _format_taste_fit(item: dict[str, Any]) -> str:
    preference = item.get("score_breakdown", {}).get("user_preference", 0)
    matches = normalize_list(item.get("taste_matches"))
    mismatches = normalize_list(item.get("taste_mismatches"))
    parts = [f"{preference}/{USER_PREFERENCE_MAX_SCORE}"]
    if matches:
        parts.append("match: " + ", ".join(matches[:4]))
    if mismatches:
        parts.append("avoid: " + ", ".join(mismatches[:3]))
    return "; ".join(parts)


def render_markdown(ranked: list[dict[str, Any]], jd_path: str | None = None, include_taste: bool | None = None) -> str:
    show_taste = _should_include_taste_column(ranked, include_taste)
    rows = []
    for index, item in enumerate(ranked, start=1):
        row = [
            index,
            item.get("name", "unnamed"),
            _format_score(item.get("score", 0)),
            item.get("raw_score", ""),
            item.get("max_raw_score", ""),
            item.get("license", ""),
            item.get("stars", ""),
            item.get("last_commit", ""),
            item.get("runnable", ""),
            item.get("compute", item.get("resources", "")),
            ", ".join(normalize_list(item.get("matched_keywords"))[:6]),
        ]
        if show_taste:
            row.append(_format_taste_fit(item))
        row.append("; ".join(normalize_list(item.get("risk_notes"))[:3]) or "无")
        rows.append(row)

    best = ranked[0] if ranked else None
    backup = ranked[1] if len(ranked) > 1 else None
    headers = [
        "Rank",
        "Name",
        "Score",
        "Raw",
        "Max Raw",
        "License",
        "Stars",
        "Last Commit",
        "Runnable",
        "Resources",
        "Matched",
    ]
    if show_taste:
        headers.append("Taste Fit")
    headers.append("Risks")

    parts = [
        "# 候选项目排序",
        "",
        f"- JD 来源：`{jd_path}`" if jd_path else "- JD 来源：未记录",
        f"- 主项目推荐：`{best.get('name')}`，score={_format_score(best.get('score'))}" if best else "- 主项目推荐：TODO",
        f"- 备选项目：`{backup.get('name')}`，score={_format_score(backup.get('score'))}" if backup else "- 备选项目：TODO",
        "- 分数说明：先计算 raw_score，再按 max_raw_score 归一化到 0-100。",
    ]
    if show_taste:
        parts.append("- 用户偏好：已启用 Taste Fit 小权重；它只用于近分排序辅助，不覆盖 JD 匹配、可运行性和风险。")
    parts.extend(
        [
            "",
            markdown_table(headers, rows),
            "",
            "## 使用说明",
            "",
            "- 这个脚本只根据显式字段打分；语义判断、JD 命中度和最终选择仍需 AI 助手/人工审阅。",
            "- 不可运行、资源要求过高、风险说明过多的项目，除非非常贴 JD，否则不建议作为主项目。",
            "- 推荐项目应尽快进入最小路径摸底、简历 4-5 行版本和面试 Q&A，而不是卡在完美复现。",
        ]
    )
    return "\n".join(parts)


def write_ranking_outputs(
    ranked: list[dict[str, Any]],
    out_dir: str | Path,
    jd_path: str | None = None,
    include_taste: bool | None = None,
) -> dict[str, str]:
    out = ensure_dir(out_dir)
    paths = {
        "candidate_score_json": str(write_json(out / "candidate_score.json", {"candidates": ranked})),
        "candidate_score_md": str(
            write_text(
                out / "candidate_score.md",
                render_markdown(ranked, jd_path=jd_path, include_taste=include_taste),
            )
        ),
    }
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rank GitHub project candidates for a computer-industry internship JD.")
    parser.add_argument("--jd", required=True, help="Path to a text file containing the target job description.")
    parser.add_argument("--candidates", required=True, help="Path to candidate JSON.")
    parser.add_argument("--taste", help="Optional path to a text file containing user project taste / preference.")
    parser.add_argument("--out", required=True, help="Output directory.")
    args = parser.parse_args(argv)

    jd_path = Path(args.jd)
    jd_text = jd_path.read_text(encoding="utf-8", errors="replace")
    candidates = parse_candidates(load_json(args.candidates))
    taste_text = None
    if args.taste:
        taste_text = Path(args.taste).read_text(encoding="utf-8", errors="replace")
    effective_taste = has_effective_taste(taste_text)
    ranked = rank_candidates(jd_text, candidates, taste_text=taste_text)
    paths = write_ranking_outputs(
        ranked,
        args.out,
        jd_path=str(jd_path),
        include_taste=effective_taste,
    )
    for label, path in paths.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

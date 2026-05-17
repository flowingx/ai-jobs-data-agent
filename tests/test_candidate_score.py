from datetime import date

from shushu_internship_tool.candidate_score import rank_candidates, render_markdown


def test_candidate_score_ranks_matchable_runnable_project_first() -> None:
    jd = "Backend Engineer Intern with FastAPI, PostgreSQL, Docker, API design, testing, and deployment experience."
    candidates = [
        {
            "name": "broken-huge-project",
            "repo_url": "https://github.com/example/broken",
            "license": "unknown",
            "stars": 3,
            "last_commit": "2021-01-01",
            "tags": ["research"],
            "jd_keywords": ["api"],
            "runnable": False,
            "compute": "large cluster",
            "mod_ideas": [],
            "risk_notes": ["no license", "requires private dataset"],
        },
        {
            "name": "tiny-backend-project",
            "repo_url": "https://github.com/example/tiny",
            "license": "Apache-2.0",
            "stars": 350,
            "last_commit": "2026-05-01",
            "tags": ["fastapi", "postgresql", "docker", "deployment"],
            "jd_keywords": ["backend", "api design", "testing", "docker"],
            "runnable": True,
            "compute": "local_docker",
            "mod_ideas": ["add JWT auth", "add Redis cache", "add integration tests"],
            "risk_notes": ["database migration needs setup"],
        },
        {
            "name": "okay-project",
            "repo_url": "https://github.com/example/okay",
            "license": "MIT",
            "stars": 80,
            "last_commit": "2025-08-01",
            "tags": ["sqlite"],
            "jd_keywords": ["database"],
            "runnable": "partial",
            "compute": "cpu",
            "mod_ideas": ["add tests"],
            "risk_notes": [],
        },
    ]

    ranked = rank_candidates(jd, candidates, today=date(2026, 5, 17))

    assert ranked[0]["name"] == "tiny-backend-project"
    assert ranked[0]["score"] > ranked[1]["score"]
    assert ranked[-1]["name"] == "broken-huge-project"

    markdown = render_markdown(ranked, jd_path="jd.txt")
    assert "主项目推荐" in markdown
    assert "tiny-backend-project" in markdown
    assert "requires private dataset" in markdown


def test_candidate_score_uses_agent_supplied_jd_matches_without_role_aliases() -> None:
    jd = "推荐算法工程师，负责视频推荐、搜索分发、大语言模型、深度学习和海量用户行为数据挖掘。"
    candidates = [
        {
            "name": "agent-selected-domain-project",
            "repo_url": "https://github.com/example/domain-project",
            "license": "MIT",
            "stars": 4500,
            "last_commit": "2026-04-01",
            "tags": ["recommendation", "pytorch", "ranking"],
            "jd_keywords": ["recommendation", "ranking", "user behavior", "deep learning"],
            "matched_jd_terms": ["推荐算法", "搜索分发", "大语言模型", "用户行为数据"],
            "runnable": True,
            "compute": "local_or_single_gpu",
            "mod_ideas": ["video proxy dataset", "ranking metrics dashboard"],
            "risk_notes": [],
        },
        {
            "name": "generic-web-admin",
            "repo_url": "https://github.com/example/admin",
            "license": "MIT",
            "stars": 300,
            "last_commit": "2026-04-01",
            "tags": ["react", "dashboard"],
            "jd_keywords": ["frontend"],
            "runnable": True,
            "compute": "local_docker",
            "mod_ideas": ["add page"],
            "risk_notes": [],
        },
    ]

    ranked = rank_candidates(jd, candidates, today=date(2026, 5, 17))

    assert ranked[0]["name"] == "agent-selected-domain-project"
    assert {"推荐算法", "搜索分发", "大语言模型", "用户行为数据"} & set(ranked[0]["matched_keywords"])

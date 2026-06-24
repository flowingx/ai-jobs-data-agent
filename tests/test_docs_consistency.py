import unittest
from pathlib import Path


ROOT = Path(__file__).parent.parent


class TestDocsConsistency(unittest.TestCase):
    def test_er_diagram_marks_summary_tables_as_derived(self):
        er_text = (ROOT / "db" / "ER_DIAGRAM.md").read_text(encoding="utf-8")
        self.assertIn("job_postings ||--o{ job_skills", er_text)
        self.assertIn("derived summary tables", er_text)
        self.assertNotIn("job_postings ||--o{ job_categories", er_text)
        self.assertNotIn("job_postings ||--o{ experience_levels", er_text)
        self.assertNotIn("job_postings ||--o{ location_summary", er_text)

    def test_submission_docs_warn_not_to_package_env_file(self):
        for filename in ("README.md", "AGENTS.md"):
            with self.subTest(filename=filename):
                text = (ROOT / filename).read_text(encoding="utf-8")
                self.assertIn(".env.example", text)
                self.assertIn(".env", text)

    def test_report_generator_avoids_overstated_marketing_terms(self):
        text = (ROOT / "generate_report.py").read_text(encoding="utf-8")
        for phrase in ("工业级硬化", "企业级硬化", "production-grade", "硬化"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, text)

    def test_remote_work_is_not_documented_as_boolean(self):
        for filename in ("app.py", "generate_report.py"):
            with self.subTest(filename=filename):
                text = (ROOT / filename).read_text(encoding="utf-8")
                self.assertNotIn("remote_work = 1", text)

    def test_streamlit_ui_copy_is_chinese(self):
        text = (ROOT / "app.py").read_text(encoding="utf-8")
        expected_chinese_copy = [
            "AI 岗位市场数据分析智能体",
            "智能问答",
            "数据浏览",
            "预置分析",
            "数据工作台",
            "搜索",
            "可视化",
            "AI 总结",
            "app-footer",
        ]
        forbidden_english_copy = [
            "Smart Query",
            "Data Browser",
            "Preset Analysis",
            "Ask a question about the job market:",
            "Visualization",
            "AI Summary",
        ]
        for phrase in expected_chinese_copy:
            with self.subTest(expected=phrase):
                self.assertIn(phrase, text)
        for phrase in forbidden_english_copy:
            with self.subTest(forbidden=phrase):
                self.assertNotIn(phrase, text)


if __name__ == "__main__":
    unittest.main()

import unittest

import pandas as pd

import app


class TestAppPresetQueries(unittest.TestCase):
    def test_example_queries_execute(self):
        if not app.DB_PATH.exists():
            self.skipTest("database not built")
        for query in app.EXAMPLE_QUERIES:
            with self.subTest(question=query["question"]):
                columns, rows, error = app.execute_sql(query["sql"])
                self.assertIsNone(error)
                self.assertGreater(len(columns), 0)
                self.assertGreater(len(rows), 0)

    def test_data_browser_visualization_queries_execute(self):
        if not app.DB_PATH.exists():
            self.skipTest("database not built")
        expected_tables = {"job_categories", "experience_levels", "location_summary", "job_skills"}
        self.assertEqual(set(app.DATA_BROWSER_VISUALIZATIONS), expected_tables)
        for table, config in app.DATA_BROWSER_VISUALIZATIONS.items():
            with self.subTest(table=table):
                columns, rows, error = app.execute_sql(config["sql"])
                self.assertIsNone(error)
                self.assertGreater(len(columns), 0)
                self.assertGreater(len(rows), 0)
                self.assertIn(config["chart"], {"bar", "pie"})

    def test_pie_chart_uses_project_chart_style(self):
        df = pd.DataFrame(
            [
                ("Hybrid", 457),
                ("Fully Remote", 297),
                ("On-site", 246),
            ],
            columns=["Work Type", "Count"],
        )
        app._setup_font()
        fig = app.draw_categorical_bar(df, ["Work Type", "Count"], "远程与现场岗位数量对比", "pie")
        try:
            ax = fig.axes[0]
            self.assertEqual(ax.get_title(loc="left"), "远程与现场岗位数量对比")
            self.assertGreater(len(ax.legend_.texts), 0)
            self.assertIn("#0f766e", app.CHART_PALETTE)
        finally:
            app.plt.close(fig)

    def test_year_skill_comparison_uses_grouped_trend_chart(self):
        rows = [
            (2025, "CUDA", 55, 212781.8),
            (2025, "Python", 382, 197000.5),
            (2026, "CUDA", 62, 199209.7),
            (2026, "Python", 560, 197840.4),
        ]
        columns = ["Year", "Skill", "Job Count", "Avg Salary (USD)"]
        sql = "SELECT posting_year, skill, COUNT(*) FROM job_skills GROUP BY posting_year, skill"
        self.assertEqual(app.auto_detect_chart(sql, columns, rows), "grouped_trend")

    def test_year_technology_alias_uses_grouped_trend_chart(self):
        rows = [
            (2025, "CUDA", 55, 212781.8),
            (2025, "Python", 382, 197000.5),
            (2026, "CUDA", 62, 199209.7),
            (2026, "Python", 560, 197840.4),
        ]
        columns = ["Year", "Technology", "Job Count", "Avg Salary (USD)"]
        sql = "SELECT posting_year AS Year, skill AS Technology, COUNT(*) FROM job_skills GROUP BY posting_year, skill"
        self.assertEqual(app.auto_detect_chart(sql, columns, rows), "grouped_trend")


if __name__ == "__main__":
    unittest.main()

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from scripts import init_db


REQUIRED_COLUMNS = [
    "job_id",
    "job_title",
    "job_category",
    "experience_level",
    "years_of_experience",
    "education_required",
    "annual_salary_usd",
    "salary_min_usd",
    "salary_max_usd",
    "city",
    "country",
    "remote_work",
    "company_size",
    "industry",
    "required_skills",
    "ai_salary_premium_pct",
    "demand_score",
    "demand_growth_yoy_pct",
    "benefits_score_10",
    "posting_year",
    "posting_month",
    "is_senior",
    "is_remote_friendly",
    "is_llm_role",
    "salary_tier",
]


class TestInitDb(unittest.TestCase):
    def _write_csv(self, path: Path, job_id: str, salary: int = 100000) -> None:
        row = {column: "" for column in REQUIRED_COLUMNS}
        row.update(
            {
                "job_id": job_id,
                "job_title": "AI Application Engineer",
                "job_category": "AI Engineer",
                "experience_level": "Entry",
                "years_of_experience": 1,
                "education_required": "Bachelor",
                "annual_salary_usd": salary,
                "salary_min_usd": salary - 10000,
                "salary_max_usd": salary + 10000,
                "city": "Shanghai",
                "country": "China",
                "remote_work": "Hybrid",
                "company_size": "100-500",
                "industry": "Software",
                "required_skills": "Python|SQL|RAG",
                "ai_salary_premium_pct": 12.5,
                "demand_score": 80,
                "demand_growth_yoy_pct": 10,
                "benefits_score_10": 8,
                "posting_year": 2026,
                "posting_month": 6,
                "is_senior": 0,
                "is_remote_friendly": 1,
                "is_llm_role": 1,
                "salary_tier": "High",
            }
        )
        pd.DataFrame([row]).to_csv(path, index=False)

    def test_build_database_is_idempotent_and_force_rebuilds(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            csv_path = root / "jobs.csv"
            db_path = root / "ai_jobs.db"
            self._write_csv(csv_path, "job-1")

            with patch.object(init_db, "CSV_PATH", csv_path), patch.object(init_db, "DB_PATH", db_path), patch.object(init_db, "DB_DIR", root):
                init_db.build_database(force=True)
                conn = sqlite3.connect(db_path)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM job_postings").fetchone()[0], 1)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM job_skills").fetchone()[0], 3)
                conn.close()

                self._write_csv(csv_path, "job-2", salary=120000)
                init_db.build_database(force=False)
                conn = sqlite3.connect(db_path)
                self.assertEqual(conn.execute("SELECT job_id FROM job_postings").fetchone()[0], "job-1")
                conn.close()

                init_db.build_database(force=True)
                conn = sqlite3.connect(db_path)
                self.assertEqual(conn.execute("SELECT job_id FROM job_postings").fetchone()[0], "job-2")
                conn.close()


if __name__ == "__main__":
    unittest.main()

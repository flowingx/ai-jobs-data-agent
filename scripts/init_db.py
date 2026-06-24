#!/usr/bin/env python3
"""Data Ingestion: Load AI Jobs Market 2025-2026 CSV into SQLite."""

import argparse
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd

CSV_PATH = Path(__file__).parent.parent / "data" / "ai_jobs_market_2025_2026.csv"
DB_DIR = Path(__file__).parent.parent / "db"
DB_PATH = DB_DIR / "ai_jobs.db"


def database_has_data(db_path: Path = DB_PATH) -> bool:
    """Return True when the existing SQLite database already has job rows."""
    if not db_path.exists():
        return False
    try:
        conn = sqlite3.connect(str(db_path))
        count = conn.execute("SELECT COUNT(*) FROM job_postings").fetchone()[0]
        return count > 0
    except sqlite3.Error:
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the raw CSV data for database ingestion."""

    # Drop duplicates
    df = df.drop_duplicates()

    # Handle missing salaries - fill with 0 and mark
    salary_cols = ["annual_salary_usd", "salary_min_usd", "salary_max_usd"]
    for col in salary_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Fill missing categorical fields
    df["job_category"] = df["job_category"].fillna("Unknown")
    df["experience_level"] = df["experience_level"].fillna("Unknown")
    df["education_required"] = df["education_required"].fillna("Unknown")
    df["city"] = df["city"].fillna("Unknown")
    df["country"] = df["country"].fillna("Unknown")
    df["remote_work"] = df["remote_work"].fillna("Unknown")
    df["company_size"] = df["company_size"].fillna("Unknown")
    df["industry"] = df["industry"].fillna("Unknown")
    df["required_skills"] = df["required_skills"].fillna("")
    df["salary_tier"] = df["salary_tier"].fillna("Unknown")

    # Ensure numeric columns are proper types
    df["years_of_experience"] = pd.to_numeric(df["years_of_experience"], errors="coerce").fillna(0).astype(int)
    df["ai_salary_premium_pct"] = pd.to_numeric(df["ai_salary_premium_pct"], errors="coerce").fillna(0).round(2)
    df["demand_score"] = pd.to_numeric(df["demand_score"], errors="coerce").fillna(0).astype(int)
    df["demand_growth_yoy_pct"] = pd.to_numeric(df["demand_growth_yoy_pct"], errors="coerce").fillna(0).round(2)
    df["benefits_score_10"] = pd.to_numeric(df["benefits_score_10"], errors="coerce").fillna(0).round(2)
    df["posting_year"] = pd.to_numeric(df["posting_year"], errors="coerce").fillna(2025).astype(int)
    df["posting_month"] = pd.to_numeric(df["posting_month"], errors="coerce").fillna(1).astype(int)

    # Boolean flags
    for col in ["is_senior", "is_remote_friendly", "is_llm_role"]:
        df[col] = df[col].fillna(0).astype(int)

    print(f"Cleaned: {len(df)} rows, {df.isnull().sum().sum()} remaining nulls")
    return df


def create_tables(conn: sqlite3.Connection):
    """Create normalized tables for the AI Jobs database."""

    conn.executescript("""
        -- Main job postings table
        CREATE TABLE IF NOT EXISTS job_postings (
            job_id TEXT PRIMARY KEY,
            job_title TEXT NOT NULL,
            job_category TEXT,
            experience_level TEXT,
            years_of_experience INTEGER,
            education_required TEXT,
            annual_salary_usd INTEGER,
            salary_min_usd INTEGER,
            salary_max_usd INTEGER,
            city TEXT,
            country TEXT,
            remote_work TEXT,
            company_size TEXT,
            industry TEXT,
            required_skills TEXT,
            ai_salary_premium_pct REAL,
            demand_score INTEGER,
            demand_growth_yoy_pct REAL,
            benefits_score_10 REAL,
            posting_year INTEGER,
            posting_month INTEGER,
            is_senior INTEGER,
            is_remote_friendly INTEGER,
            is_llm_role INTEGER,
            salary_tier TEXT
        );

        -- Skills dimension table (for joins and analysis)
        CREATE TABLE IF NOT EXISTS job_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            skill TEXT NOT NULL,
            FOREIGN KEY (job_id) REFERENCES job_postings(job_id)
        );

        -- Job categories summary
        CREATE TABLE IF NOT EXISTS job_categories (
            category TEXT PRIMARY KEY,
            job_count INTEGER,
            avg_salary REAL,
            avg_demand_score REAL
        );

        -- Experience level summary
        CREATE TABLE IF NOT EXISTS experience_levels (
            level TEXT PRIMARY KEY,
            job_count INTEGER,
            avg_salary REAL,
            avg_years_experience REAL
        );

        -- Country/City summary
        CREATE TABLE IF NOT EXISTS location_summary (
            country TEXT,
            city TEXT,
            job_count INTEGER,
            avg_salary REAL,
            PRIMARY KEY (country, city)
        );

        -- Create indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_postings_category ON job_postings(job_category);
        CREATE INDEX IF NOT EXISTS idx_postings_country ON job_postings(country);
        CREATE INDEX IF NOT EXISTS idx_postings_remote ON job_postings(remote_work);
        CREATE INDEX IF NOT EXISTS idx_postings_salary ON job_postings(annual_salary_usd);
        CREATE INDEX IF NOT EXISTS idx_postings_experience ON job_postings(experience_level);
        CREATE INDEX IF NOT EXISTS idx_skills_job ON job_skills(job_id);
        CREATE INDEX IF NOT EXISTS idx_skills_skill ON job_skills(skill);
    """)


def populate_dimension_tables(conn: sqlite3.Connection, df: pd.DataFrame):
    """Populate aggregated/summary tables for faster queries."""

    # Job categories summary
    cat_stats = df.groupby("job_category").agg(
        job_count=("job_id", "count"),
        avg_salary=("annual_salary_usd", "mean"),
        avg_demand=("demand_score", "mean")
    ).reset_index()
    for _, row in cat_stats.iterrows():
        conn.execute(
            "INSERT OR REPLACE INTO job_categories VALUES (?, ?, ?, ?)",
            (row["job_category"], int(row["job_count"]), round(row["avg_salary"], 2), round(row["avg_demand"], 2))
        )

    # Experience levels summary
    exp_stats = df.groupby("experience_level").agg(
        job_count=("job_id", "count"),
        avg_salary=("annual_salary_usd", "mean"),
        avg_years=("years_of_experience", "mean")
    ).reset_index()
    for _, row in exp_stats.iterrows():
        conn.execute(
            "INSERT OR REPLACE INTO experience_levels VALUES (?, ?, ?, ?)",
            (row["experience_level"], int(row["job_count"]), round(row["avg_salary"], 2), round(row["avg_years"], 2))
        )

    # Location summary
    loc_stats = df.groupby(["country", "city"]).agg(
        job_count=("job_id", "count"),
        avg_salary=("annual_salary_usd", "mean")
    ).reset_index()
    for _, row in loc_stats.iterrows():
        conn.execute(
            "INSERT OR REPLACE INTO location_summary VALUES (?, ?, ?, ?)",
            (row["country"], row["city"], int(row["job_count"]), round(row["avg_salary"], 2))
        )

    conn.commit()


def populate_skills(conn: sqlite3.Connection, df: pd.DataFrame):
    """Explode pipe-delimited skills into individual rows."""
    skills_data = []
    for _, row in df.iterrows():
        skills_str = str(row["required_skills"])
        if skills_str and skills_str != "nan":
            for skill in skills_str.split("|"):
                skill = skill.strip()
                if skill:
                    skills_data.append((row["job_id"], skill))

    conn.executemany("INSERT INTO job_skills (job_id, skill) VALUES (?, ?)", skills_data)
    conn.commit()
    print(f"Inserted {len(skills_data)} skill records")


def build_database(force: bool = False):
    """Main entry point: read CSV, clean, load into SQLite."""
    if database_has_data(DB_PATH) and not force:
        print(f"Database already initialized with data. Skipping full recreation: {DB_PATH}")
        print("Use --force to rebuild from CSV.")
        return

    if not CSV_PATH.exists():
        print(f"ERROR: CSV not found at {CSV_PATH}")
        print("Run: kaggle datasets download -d alitaqishah/ai-jobs-market-2025-2026-salaries -p data --unzip")
        return

    print(f"Reading CSV: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    print(f"Raw rows: {len(df)}")

    df = clean_dataframe(df)

    DB_DIR.mkdir(parents=True, exist_ok=True)
    temp_db = Path(tempfile.gettempdir()) / f"{DB_PATH.stem}.building{DB_PATH.suffix}"
    if temp_db.exists():
        temp_db.unlink()

    conn = sqlite3.connect(str(temp_db))
    create_tables(conn)

    # Insert main job postings
    df.to_sql("job_postings", conn, if_exists="append", index=False)
    print(f"Inserted {len(df)} job postings")

    # Populate dimension tables
    populate_dimension_tables(conn, df)

    # Populate skills table
    populate_skills(conn, df)

    # Print summary
    cursor = conn.execute("SELECT COUNT(*) FROM job_postings")
    total = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM job_skills")
    skill_count = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(DISTINCT skill) FROM job_skills")
    unique_skills = cursor.fetchone()[0]

    print(f"\n{'='*50}")
    print(f"Database created: {DB_PATH}")
    print(f"  Job postings: {total}")
    print(f"  Skill records: {skill_count}")
    print(f"  Unique skills: {unique_skills}")
    print(f"{'='*50}")

    conn.close()
    shutil.copy2(temp_db, DB_PATH)
    temp_db.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the AI jobs SQLite database from CSV.")
    parser.add_argument("--force", action="store_true", help="Rebuild the database even if it already has data.")
    args = parser.parse_args()
    build_database(force=args.force)

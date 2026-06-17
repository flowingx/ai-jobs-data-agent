#!/usr/bin/env python3
"""Auto-generate Mermaid ER diagram from SQLite schema."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "ai_jobs.db"
OUTPUT = Path(__file__).parent.parent / "db" / "ER_DIAGRAM.md"


def get_schema(db_path: str) -> dict:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    schema = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = []
        for row in cursor.fetchall():
            cid, name, ctype, notnull, default, pk = row
            columns.append({
                "name": name,
                "type": ctype,
                "pk": bool(pk),
                "notnull": bool(notnull),
            })

        cursor.execute(f"PRAGMA foreign_key_list({table})")
        fks = []
        for row in cursor.fetchall():
            id, seq, table_name, from_col, to_col, on_update, on_delete, match = row
            fks.append({"from": from_col, "to_table": table_name, "to_col": to_col})

        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]

        schema[table] = {
            "columns": columns,
            "fks": fks,
            "row_count": row_count,
        }

    conn.close()
    return schema


def mermaid_type(ctype: str) -> str:
    t = ctype.upper()
    if "INT" in t:
        return "int"
    if "REAL" in t or "FLOAT" in t or "DOUBLE" in t or "NUMERIC" in t:
        return "float"
    if "BLOB" in t:
        return "blob"
    return "string"


def generate_mermaid(schema: dict) -> str:
    lines = ["erDiagram"]

    table_order = ["job_postings", "job_skills", "job_categories",
                   "experience_levels", "location_summary"]

    for table in table_order:
        if table not in schema:
            continue
        info = schema[table]
        lines.append(f"    {table} {{")

        for col in info["columns"]:
            mtype = mermaid_type(col["type"])
            annotations = []
            if col["pk"]:
                annotations.append("PK")
            if col["notnull"]:
                annotations.append("NOT NULL")
            ann_str = " ".join(annotations)
            if ann_str:
                ann_str = f" {ann_str}"
            lines.append(f"        {mtype} {col['name']}{ann_str}")

        lines.append("    }")
        lines.append("")

    relations = [
        ("job_postings", "1", "--", "o{", "job_skills", "has many skills"),
        ("job_postings", "1", "--", "o{", "job_categories", "aggregated by category"),
        ("job_postings", "1", "--", "o{", "experience_levels", "aggregated by experience"),
        ("job_postings", "1", "--", "o{", "location_summary", "aggregated by location"),
    ]

    for src, c1, line, c2, dst, label in relations:
        lines.append(f"    {src} ||{line}{c2} {dst} : \"{label}\"")

    return "\n".join(lines)


def main():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    print(f"Scanning schema: {DB_PATH}")
    schema = get_schema(str(DB_PATH))

    for table, info in schema.items():
        print(f"  {table}: {len(info['columns'])} columns, {info['row_count']} rows")

    mermaid = generate_mermaid(schema)

    OUTPUT.write_text(f"# ER Diagram (Auto-generated)\n\n```mermaid\n{mermaid}\n```\n",
                       encoding="utf-8")
    print(f"\nMermaid ER diagram saved: {OUTPUT}")
    print(f"\n{'='*60}")
    print(mermaid)
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

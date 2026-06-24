import unittest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.llm_utils import (
    clean_llm_output,
    extract_sql,
    generate_sql_with_llm,
    validate_readonly_sql,
    MAX_SQL_LENGTH,
    MAX_OR_CHAINS,
)


class FailingLLM:
    def invoke(self, messages):
        raise AssertionError("LLM should not be called for a deterministic known query")


class TestCleanLlmOutput(unittest.TestCase):
    def test_strips_think_tags(self):
        text = "<think>thinking</think>Hello world"
        self.assertEqual(clean_llm_output(text), "Hello world")

    def test_strips_unclosed_think_tag(self):
        text = "<think>reasoning...</think>Hello world"
        self.assertEqual(clean_llm_output(text), "Hello world")

    def test_unclosed_think_consumes_remaining(self):
        text = "<think>reasoning...Hello world"
        self.assertEqual(clean_llm_output(text), "")

    def test_strips_opening_think_tag(self):
        text = "<think>analysis</think>Answer"
        self.assertEqual(clean_llm_output(text), "Answer")

    def test_strips_multiple_think_blocks(self):
        text = "<think>First</think><think>Second</think>Final"
        self.assertEqual(clean_llm_output(text), "Final")

    def test_plain_text_unchanged(self):
        text = "SELECT * FROM job_postings"
        self.assertEqual(clean_llm_output(text), text)

    def test_strips_leading_trailing_whitespace(self):
        text = "  <think>x</think>  result  "
        self.assertEqual(clean_llm_output(text), "result")


class TestExtractSql(unittest.TestCase):
    def test_markdown_fenced(self):
        text = "```sql\nSELECT skill FROM job_skills\n```"
        self.assertEqual(extract_sql(text), "SELECT skill FROM job_skills")

    def test_markdown_fenced_no_lang(self):
        text = "```\nSELECT skill FROM job_skills\n```"
        self.assertEqual(extract_sql(text), "SELECT skill FROM job_skills")

    def test_plain_select(self):
        text = "SELECT skill FROM job_skills"
        self.assertEqual(extract_sql(text), "SELECT skill FROM job_skills")

    def test_plain_with_keyword(self):
        text = "WITH cte AS (SELECT 1) SELECT * FROM cte"
        self.assertEqual(extract_sql(text), "WITH cte AS (SELECT 1) SELECT * FROM cte")

    def test_strips_single_line_comment(self):
        text = "-- this is a comment\nSELECT skill FROM job_skills"
        self.assertEqual(extract_sql(text), "SELECT skill FROM job_skills")

    def test_strips_block_comment(self):
        text = "/* comment */ SELECT skill FROM job_skills"
        self.assertEqual(extract_sql(text), "SELECT skill FROM job_skills")

    def test_strips_think_and_extracts_sql(self):
        text = "<think>Let me think about this...</think>\n```sql\nSELECT COUNT(*) FROM job_postings\n```"
        self.assertEqual(extract_sql(text), "SELECT COUNT(*) FROM job_postings")

    def test_truncates_long_or_chain(self):
        or_conditions = " OR ".join([f"skill = '{i}'" for i in range(15)])
        sql = f"SELECT * FROM job_skills WHERE {or_conditions}"
        result = extract_sql(sql)
        or_count = result.upper().count(" OR ")
        self.assertLessEqual(or_count, MAX_OR_CHAINS)
        self.assertIn("LIMIT 50", result.upper())

    def test_long_or_chain_preserved_when_under_limit(self):
        or_conditions = " OR ".join([f"skill = '{i}'" for i in range(5)])
        sql = f"SELECT * FROM job_skills WHERE {or_conditions}"
        result = extract_sql(sql)
        or_count = result.upper().count(" OR ")
        self.assertEqual(or_count, 4)
        self.assertNotIn("LIMIT 50", result.upper())

    def test_truncates_long_sql(self):
        sql = "SELECT " + ", ".join([f"col{i}" for i in range(200)])
        result = extract_sql(sql)
        self.assertLessEqual(len(result), MAX_SQL_LENGTH)

    def test_strips_trailing_semicolon(self):
        sql = "SELECT skill FROM job_skills;"
        self.assertEqual(extract_sql(sql), "SELECT skill FROM job_skills")

    def test_empty_input_returns_empty(self):
        self.assertEqual(extract_sql(""), "")

    def test_noise_before_select_is_stripped(self):
        text = "Here is your SQL:\nSELECT skill FROM job_skills"
        self.assertEqual(extract_sql(text), "SELECT skill FROM job_skills")

    def test_markdown_with_surrounding_text(self):
        text = """Here's the query:

```sql
SELECT city, COUNT(*) FROM job_postings GROUP BY city
```

Let me know if you need anything else."""
        self.assertEqual(extract_sql(text), "SELECT city, COUNT(*) FROM job_postings GROUP BY city")


class TestValidateReadonlySql(unittest.TestCase):
    def test_allows_select(self):
        validate_readonly_sql("SELECT skill FROM job_skills LIMIT 5")

    def test_allows_with_select(self):
        validate_readonly_sql("WITH top_skills AS (SELECT skill FROM job_skills) SELECT * FROM top_skills")

    def test_rejects_write_keywords(self):
        bad_sql = [
            "DROP TABLE job_postings",
            "UPDATE job_postings SET annual_salary_usd = 0",
            "INSERT INTO job_skills(job_id, skill) VALUES ('1', 'Python')",
            "DELETE FROM job_skills",
            "CREATE TABLE x(id int)",
            "PRAGMA writable_schema=ON",
        ]
        for sql in bad_sql:
            with self.subTest(sql=sql):
                with self.assertRaises(ValueError):
                    validate_readonly_sql(sql)

    def test_rejects_multiple_statements(self):
        with self.assertRaises(ValueError):
            validate_readonly_sql("SELECT * FROM job_postings; SELECT * FROM job_skills")

    def test_rejects_with_write_statement(self):
        with self.assertRaises(ValueError):
            validate_readonly_sql("WITH x AS (SELECT 1) UPDATE job_postings SET annual_salary_usd = 0")


class TestKnownQuestionSql(unittest.TestCase):
    def test_remote_vs_onsite_salary_uses_text_work_type_values(self):
        sql = generate_sql_with_llm(FailingLLM(), "远程与现场 AI 岗位的平均薪资分别是多少？")
        self.assertIn("remote_work IN ('Fully Remote', 'Hybrid')", sql)
        self.assertIn("GROUP BY", sql.upper())
        self.assertNotIn("remote_work = 1", sql)

    def test_cuda_python_year_comparison_uses_year_then_skill(self):
        sql = generate_sql_with_llm(FailingLLM(), "对比 CUDA 和 Python 在不同年份的岗位数量和平均薪资")
        self.assertIn('jp.posting_year AS "Year"', sql)
        self.assertIn('js.skill AS "Skill"', sql)
        self.assertIn("LOWER(js.skill) IN ('cuda', 'python')", sql)
        self.assertLess(sql.index('jp.posting_year AS "Year"'), sql.index('js.skill AS "Skill"'))


if __name__ == "__main__":
    unittest.main()

import unittest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.llm_utils import clean_llm_output, extract_sql, MAX_SQL_LENGTH, MAX_OR_CHAINS


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


if __name__ == "__main__":
    unittest.main()

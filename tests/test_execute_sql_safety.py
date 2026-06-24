import inspect
import unittest
from unittest.mock import patch

import app
from scripts import data_agent


class TestExecuteSqlSafety(unittest.TestCase):
    def test_app_validates_sql_before_opening_connection(self):
        source = inspect.getsource(app.execute_sql)
        self.assertLess(source.index("validate_readonly_sql"), source.index("sqlite3.connect"))

    def test_cli_agent_validates_sql_before_opening_connection(self):
        source = inspect.getsource(data_agent.execute_sql)
        self.assertLess(source.index("validate_readonly_sql"), source.index("sqlite3.connect"))

    def test_execute_sql_uses_read_only_sqlite_uri(self):
        for fn in (app.execute_sql, data_agent.execute_sql):
            with self.subTest(function=fn.__module__):
                source = inspect.getsource(fn)
                self.assertIn("mode=ro", source)
                self.assertIn("uri=True", source)

    def test_app_rejects_dangerous_sql_before_connecting(self):
        with patch("app.sqlite3.connect") as connect:
            columns, rows, error = app.execute_sql("DROP TABLE job_postings")
        self.assertEqual(columns, [])
        self.assertEqual(rows, [])
        self.assertIsNotNone(error)
        connect.assert_not_called()

    def test_cli_agent_rejects_dangerous_sql_before_connecting(self):
        with patch("scripts.data_agent.sqlite3.connect") as connect:
            columns, rows, error = data_agent.execute_sql("UPDATE job_postings SET annual_salary_usd = 0")
        self.assertEqual(columns, [])
        self.assertEqual(rows, [])
        self.assertIsNotNone(error)
        connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()

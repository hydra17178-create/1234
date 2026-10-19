"""Unit tests for the plain-text session report."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from bookclub.services import SessionReportService


class SessionReportServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.time_in = datetime(2026, 10, 19, 9, 5, 7)
        self.time_out = datetime(2026, 10, 19, 11, 45, 12)

    def test_render_report_has_exact_header_and_time_format(self) -> None:
        report = SessionReportService.render_report(
            "reader",
            self.time_in,
            self.time_out,
        )
        self.assertEqual(
            "+--------+---------------------+---------------------+\n"
            "| login  | time_in             | time_out            |\n"
            "+--------+---------------------+---------------------+\n"
            "| reader | 19.10.2026 09:05:07 | 19.10.2026 11:45:12 |\n"
            "+--------+---------------------+---------------------+\n",
            report,
        )

    def test_write_and_append_preserve_complete_tables(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "sessions.txt"
            SessionReportService.write_report(
                report_path,
                "first",
                self.time_in,
                self.time_out,
            )
            SessionReportService.write_report(
                report_path,
                "second",
                self.time_in,
                self.time_out,
                append=True,
            )
            report = report_path.read_text(encoding="utf-8")

        self.assertEqual(2, report.count("time_in"))
        self.assertEqual(2, report.count("19.10.2026 09:05:07"))
        self.assertIn("\n\n+", report)

    def test_invalid_session_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SessionReportService.format_session("bad|login", self.time_in, self.time_out)
        with self.assertRaises(ValueError):
            SessionReportService.format_session("reader", self.time_out, self.time_in)


if __name__ == "__main__":
    unittest.main()

"""Tests for analyzer.py CLI and print functions in other modules."""
import sys
import pytest
from unittest.mock import patch, MagicMock
import analyzer
import summary
import anomalies
class TestAnalyzerCLI:
    @patch("analyzer.sys.argv", ["analyzer.py"])
    def test_no_args_exits(self):
        with pytest.raises(SystemExit) as exc:
            analyzer.main()
        assert exc.value.code == 1
    @patch("analyzer.sys.argv", ["analyzer.py", "fake.tlog", "--summary"])
    @patch("analyzer.parse_log")
    @patch("analyzer.generate_summary")
    @patch("analyzer.print_summary")
    def test_summary_flag(self, mock_print, mock_gen, mock_parse, empty_data):
        mock_parse.return_value = empty_data
        empty_data["meta"]["parsed_messages"] = 10
        mock_gen.return_value = {"duration_formatted": "0m 0s", "battery_start": -1}
        analyzer.main()
        mock_parse.assert_called_once()
        mock_gen.assert_called_once()
        mock_print.assert_called_once()
    @patch("analyzer.sys.argv", ["analyzer.py", "fake.tlog", "--all"])
    @patch("analyzer.parse_log")
    @patch("analyzer.generate_summary")
    @patch("analyzer.export_all")
    @patch("analyzer.generate_all_graphs")
    @patch("analyzer.run_all_checks")
    def test_all_flag(self, mock_checks, mock_graphs, mock_export, mock_summary, mock_parse, empty_data):
        empty_data["meta"]["parsed_messages"] = 10
        mock_parse.return_value = empty_data
        mock_summary.return_value = {
            "battery_start": -1,
            "duration_formatted": "0m 0s",
            "total_messages": 10,
            "parsed_messages": 10,
            "max_altitude": 0,
            "avg_speed": 0,
            "max_speed": 0,
            "total_distance": 0,
            "max_displacement": 0,
            "peak_climb_rate": 0,
            "peak_descent_rate": 0,
            "gps_sample_count": 0,
            "attitude_sample_count": 0,
            "events": []
        }
        analyzer.main()
        mock_summary.assert_called_once()
        mock_export.assert_called_once()
        mock_graphs.assert_called_once()
        mock_checks.assert_called_once()
    @patch("analyzer.sys.argv", ["analyzer.py", "fake.tlog", "--summary"])
    @patch("analyzer.parse_log")
    def test_no_messages_exits(self, mock_parse, empty_data):
        mock_parse.return_value = empty_data
        with pytest.raises(SystemExit) as exc:
            analyzer.main()
        assert exc.value.code == 0
    @patch("analyzer.sys.argv", ["analyzer.py", "fake.tlog", "--summary"])
    @patch("analyzer.parse_log")
    def test_file_not_found_exits(self, mock_parse):
        mock_parse.side_effect = FileNotFoundError("Missing")
        with pytest.raises(SystemExit) as exc:
            analyzer.main()
        assert exc.value.code == 1
    @patch("analyzer.sys.argv", ["analyzer.py", "fake.tlog", "--report"])
    @patch("analyzer.parse_log")
    @patch("analyzer.generate_report")
    def test_report_flag(self, mock_report, mock_parse, empty_data):
        empty_data["meta"]["parsed_messages"] = 10
        mock_parse.return_value = empty_data
        mock_report.return_value = "output/flight_report.pdf"
        analyzer.main()
        mock_parse.assert_called_once()
        mock_report.assert_called_once()
    @patch("analyzer.sys.argv", ["analyzer.py", "--batch", "nonexistent_folder"])
    def test_batch_invalid_folder_exits(self):
        with pytest.raises(SystemExit) as exc:
            analyzer.main()
        assert exc.value.code == 1
    def test_find_log_files(self, tmp_path):
        (tmp_path / "test.tlog").touch()
        (tmp_path / "test.bin").touch()
        (tmp_path / "test.txt").touch()
        files = analyzer.find_log_files(str(tmp_path))
        assert len(files) == 2
        assert any("test.tlog" in f for f in files)
        assert any("test.bin" in f for f in files)
    def test_find_log_files_empty(self, tmp_path):
        files = analyzer.find_log_files(str(tmp_path))
        assert len(files) == 0
    def test_print_batch_table(self, capsys):
        results = [
            {
                "file": "test.tlog",
                "duration": "5m 30s",
                "max_alt": 50.0,
                "max_speed": 15.0,
                "distance": 500.0,
                "battery_start": 100,
                "battery_end": 80,
                "warnings": 0,
            },
            {
                "file": "test.bin",
                "duration": "10m 0s",
                "max_alt": 75.0,
                "max_speed": 20.0,
                "distance": 1000.0,
                "battery_start": -1,
                "battery_end": -1,
                "warnings": 2,
            },
        ]
        analyzer._print_batch_table(results)
        captured = capsys.readouterr()
        assert "BATCH ANALYSIS COMPARISON TABLE" in captured.out
        assert "test.tlog" in captured.out
        assert "test.bin" in captured.out
        assert "Total files analyzed: 2" in captured.out
class TestPrintFunctions:
    def test_print_summary(self, capsys):
        stats = {
            "duration_seconds": 10,
            "duration_formatted": "0m 10s",
            "total_messages": 100,
            "parsed_messages": 50,
            "max_altitude": 10.0,
            "avg_speed": 5.0,
            "max_speed": 10.0,
            "total_distance": 50.0,
            "max_displacement": 20.0,
            "peak_climb_rate": 2.0,
            "peak_descent_rate": 1.0,
            "battery_start": 100,
            "battery_end": 90,
            "battery_used": 10,
            "gps_sample_count": 5,
            "attitude_sample_count": 5,
            "events": [
                {"timestamp": 123.0, "datetime": "2023-11-14 12:00:00", "name": "Test Event"}
            ]
        }
        summary.print_summary(stats)
        captured = capsys.readouterr()
        assert "FLIGHT SUMMARY" in captured.out
        assert "0m 10s" in captured.out
        assert "Test Event" in captured.out
    def test_print_summary_no_battery(self, capsys):
        stats = {
            "duration_formatted": "0m 10s",
            "total_messages": 100,
            "parsed_messages": 50,
            "max_altitude": 10.0,
            "avg_speed": 5.0,
            "max_speed": 10.0,
            "total_distance": 50.0,
            "max_displacement": 20.0,
            "peak_climb_rate": 2.0,
            "peak_descent_rate": 1.0,
            "battery_start": -1,
            "battery_end": -1,
            "battery_used": 0,
            "gps_sample_count": 5,
            "attitude_sample_count": 5,
        }
        summary.print_summary(stats)
        captured = capsys.readouterr()
        assert "Not available" in captured.out
    def test_print_warnings(self, capsys):
        warnings = ["LOW BATTERY at T+10s", "ALTITUDE DROP"]
        anomalies.print_warnings(warnings)
        captured = capsys.readouterr()
        assert "FLIGHT WARNINGS" in captured.out
        assert "Found 2 warning(s)" in captured.out
        assert "LOW BATTERY at T+10s" in captured.out
    def test_print_warnings_clean(self, capsys):
        anomalies.print_warnings([])
        captured = capsys.readouterr()
        assert "No warnings detected" in captured.out

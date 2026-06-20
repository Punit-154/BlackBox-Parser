"""Tests for reporter.py PDF report generation."""
import os
import pytest
from unittest.mock import patch
import reporter
class TestReporter:
    def test_generate_report_creates_pdf(self, sample_data, tmp_path):
        output_dir = str(tmp_path)
        result = reporter.generate_report(sample_data, output_dir=output_dir)
        assert result is not None
        assert os.path.isfile(result)
        assert result.endswith("flight_report.pdf")
        size = os.path.getsize(result)
        assert size > 1000
    def test_generate_report_empty_data(self, empty_data, tmp_path):
        output_dir = str(tmp_path)
        result = reporter.generate_report(empty_data, output_dir=output_dir)
        assert result is not None
        assert os.path.isfile(result)
    def test_generate_report_with_config(self, sample_data, sample_config, tmp_path):
        output_dir = str(tmp_path)
        result = reporter.generate_report(
            sample_data, output_dir=output_dir, config=sample_config
        )
        assert result is not None
        assert os.path.isfile(result)
    def test_generate_report_with_warnings(self, low_battery_data, tmp_path):
        output_dir = str(tmp_path)
        result = reporter.generate_report(low_battery_data, output_dir=output_dir)
        assert result is not None
        assert os.path.isfile(result)
    def test_generate_report_with_bin_data(self, bin_style_data, tmp_path):
        output_dir = str(tmp_path)
        result = reporter.generate_report(bin_style_data, output_dir=output_dir)
        assert result is not None
        assert os.path.isfile(result)
class TestFlightReportPDF:
    def test_title_page(self, sample_data, tmp_path):
        pdf = reporter.FlightReport("test.tlog")
        pdf.alias_nb_pages()
        pdf.add_title_page()
        output_path = str(tmp_path / "test.pdf")
        pdf.output(output_path)
        assert os.path.isfile(output_path)
    def test_summary_section(self, sample_data, tmp_path):
        from summary import generate_summary
        stats = generate_summary(sample_data)
        pdf = reporter.FlightReport("test.tlog")
        pdf.alias_nb_pages()
        pdf.add_summary_section(stats)
        output_path = str(tmp_path / "test.pdf")
        pdf.output(output_path)
        assert os.path.isfile(output_path)
    def test_warnings_section_no_warnings(self, tmp_path):
        pdf = reporter.FlightReport("test.tlog")
        pdf.alias_nb_pages()
        pdf.add_warnings_section([])
        output_path = str(tmp_path / "test.pdf")
        pdf.output(output_path)
        assert os.path.isfile(output_path)
    def test_warnings_section_with_warnings(self, tmp_path):
        warnings = ["LOW BATTERY at 20%", "ALTITUDE DROP of 15m"]
        pdf = reporter.FlightReport("test.tlog")
        pdf.alias_nb_pages()
        pdf.add_warnings_section(warnings)
        output_path = str(tmp_path / "test.pdf")
        pdf.output(output_path)
        assert os.path.isfile(output_path)

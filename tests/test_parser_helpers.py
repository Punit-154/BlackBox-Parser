"""Tests for parser.py — helper and validation functions.
These tests do NOT require pymavlink or real log files.
"""
import os
import pytest
from parser import (
    validate_log_file,
    validate_tlog_file,
    _safe_datetime,
    _make_empty_data,
    _post_process_bin_data,
)
class TestValidation:
    def test_validate_log_file_missing(self):
        with pytest.raises(FileNotFoundError):
            validate_log_file("nonexistent.tlog")
    def test_validate_log_file_wrong_ext(self, tmp_path):
        bad_file = tmp_path / "test.csv"
        bad_file.write_text("dummy")
        with pytest.raises(ValueError, match="Unsupported file type"):
            validate_log_file(str(bad_file))
    def test_validate_log_file_tlog(self, tmp_path):
        f = tmp_path / "test.tlog"
        f.write_text("dummy")
        path = validate_log_file(str(f))
        assert path.endswith("test.tlog")
    def test_validate_log_file_bin(self, tmp_path):
        f = tmp_path / "test.bin"
        f.write_text("dummy")
        path = validate_log_file(str(f))
        assert path.endswith("test.bin")
    def test_validate_tlog_rejects_bin(self, tmp_path):
        f = tmp_path / "test.bin"
        f.write_text("dummy")
        with pytest.raises(ValueError, match="Expected a .tlog"):
            validate_tlog_file(str(f))
class TestSafeDatetime:
    def test_safe_datetime_valid(self):
        dt = _safe_datetime(1700000000.0)
        assert dt is not None
        assert "2023-11" in dt
    def test_safe_datetime_boot_relative(self):
        dt = _safe_datetime(123.0)
        assert dt is None
class TestMakeEmptyData:
    def test_make_empty_data(self):
        data = _make_empty_data("/fake/path.tlog")
        for key in ["gps", "position", "battery", "attitude", "events"]:
            assert isinstance(data[key], list)
            assert len(data[key]) == 0
        assert data["meta"]["filepath"] == "/fake/path.tlog"
        assert data["meta"]["total_messages"] == 0
class TestPostProcessBinData:
    def test_post_process_altitude(self):
        data = _make_empty_data("test.bin")
        data["gps"] = [
            {"timestamp": 100, "datetime": None, "lat": 0.0, "lon": 0.0, "alt": 150.0},
            {"timestamp": 105, "datetime": None, "lat": 0.0, "lon": 0.0, "alt": 160.0},
        ]
        _post_process_bin_data(data)
        assert len(data["position"]) == 2
        assert data["position"][0]["relative_alt"] == 0.0                 
        assert data["position"][1]["relative_alt"] == 10.0                
    def test_post_process_battery_pct(self):
        data = _make_empty_data("test.bin")
        data["battery"] = [
            {"voltage": 12.6, "current": 5.0, "battery_remaining": None},          
            {"voltage": 11.55, "current": 5.0, "battery_remaining": None},         
            {"voltage": 10.5, "current": 5.0, "battery_remaining": None},           
        ]
        _post_process_bin_data(data)
        assert data["battery"][0]["battery_remaining"] == 100
        assert data["battery"][1]["battery_remaining"] == 50
        assert data["battery"][2]["battery_remaining"] == 0
    def test_post_process_custom_battery_config(self, sample_config):
        sample_config["battery_estimation"]["cell_voltage_full"] = 4.1
        sample_config["battery_estimation"]["cell_voltage_empty"] = 3.3
        data = _make_empty_data("test.bin")
        data["battery"] = [
            {"voltage": 12.3, "current": 5.0, "battery_remaining": None},                    
            {"voltage": 9.9, "current": 5.0, "battery_remaining": None},                      
        ]
        _post_process_bin_data(data, config=sample_config)
        assert data["battery"][0]["battery_remaining"] == 100
        assert data["battery"][1]["battery_remaining"] == 0

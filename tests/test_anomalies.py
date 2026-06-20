"""Tests for anomalies.py — anomaly detection functions."""
import math
from anomalies import (
    check_low_battery,
    check_altitude_drop,
    check_excessive_attitude,
    run_all_checks,
    _ts_to_time_str,
)
BASE_TS = 1700000000.0
class TestTsToTimeStr:
    def test_epoch_timestamp(self):
        """Valid epoch timestamp → HH:MM:SS format."""
        result = _ts_to_time_str(1700000000.0)
        assert ":" in result
        parts = result.split(":")
        assert len(parts) == 3
    def test_boot_relative_timestamp(self):
        """Boot-relative timestamp (< year 2000) → T+Ns label."""
        result = _ts_to_time_str(123.0)
        assert result == "T+123s"
    def test_zero_timestamp(self):
        """Zero timestamp is boot-relative."""
        result = _ts_to_time_str(0.0)
        assert result.startswith("T+")
class TestCheckLowBattery:
    def test_no_warnings_clean_flight(self, sample_data):
        """Battery stays above 20 % throughout → no warnings."""
        warnings = check_low_battery(sample_data)
        assert warnings == []
    def test_low_battery_triggered(self, low_battery_data):
        """Battery drops below 20 % → exactly 1 warning."""
        warnings = check_low_battery(low_battery_data)
        assert len(warnings) == 1
        assert "LOW BATTERY" in warnings[0]
    def test_low_battery_warns_once(self, low_battery_data):
        """Even with multiple sub-threshold entries, only 1 warning."""
        warnings = check_low_battery(low_battery_data)
        assert len(warnings) == 1
    def test_low_battery_none_values(self, bin_style_data):
        """None battery_remaining values are safely skipped."""
        warnings = check_low_battery(bin_style_data)
        assert isinstance(warnings, list)
    def test_low_battery_negative_values(self, empty_data):
        """Negative sentinel values (-1) are skipped."""
        empty_data["battery"] = [
            {"timestamp": BASE_TS, "battery_remaining": -1, "voltage": 12.0, "current": 5.0},
            {"timestamp": BASE_TS + 5, "battery_remaining": -1, "voltage": 11.5, "current": 6.0},
        ]
        warnings = check_low_battery(empty_data)
        assert warnings == []
    def test_low_battery_custom_threshold(self, sample_data):
        """Custom higher threshold (99 %) catches the 95 % start battery."""
        warnings = check_low_battery(sample_data, threshold=99)
        assert len(warnings) == 1
        assert "LOW BATTERY" in warnings[0]
class TestCheckAltitudeDrop:
    def test_altitude_drop_detected(self, altitude_drop_data):
        """15 m drop exceeds default 10 m threshold → warning."""
        warnings = check_altitude_drop(altitude_drop_data)
        assert len(warnings) >= 1
        assert "ALTITUDE DROP" in warnings[0]
    def test_altitude_drop_below_threshold(self, sample_data):
        """Normal altitude changes → no warning."""
        warnings = check_altitude_drop(sample_data)
        for w in warnings:
            assert "ALTITUDE DROP" in w                                
    def test_altitude_drop_none_values(self, empty_data):
        """Entries with None relative_alt are filtered out."""
        empty_data["position"] = [
            {"timestamp": BASE_TS,     "relative_alt": None},
            {"timestamp": BASE_TS + 3, "relative_alt": 50.0},
            {"timestamp": BASE_TS + 6, "relative_alt": None},
            {"timestamp": BASE_TS + 9, "relative_alt": 45.0},
        ]
        warnings = check_altitude_drop(empty_data)
        assert isinstance(warnings, list)
    def test_altitude_drop_custom_threshold(self, altitude_drop_data):
        """Tighter threshold (5 m) catches smaller drops too."""
        warnings = check_altitude_drop(altitude_drop_data, threshold=5.0)
        assert len(warnings) >= 1
    def test_altitude_drop_empty(self, empty_data):
        """No position data → no warnings, no crash."""
        warnings = check_altitude_drop(empty_data)
        assert warnings == []
class TestCheckExcessiveAttitude:
    def test_excessive_roll(self, excessive_attitude_data):
        """Roll of 7.0 rad (~401°) exceeds default 360° limit."""
        warnings = check_excessive_attitude(excessive_attitude_data)
        roll_warnings = [w for w in warnings if "ROLL" in w]
        assert len(roll_warnings) >= 1
    def test_excessive_pitch(self, excessive_attitude_data):
        """Pitch of 7.0 rad (~401°) exceeds default 360° limit."""
        warnings = check_excessive_attitude(excessive_attitude_data)
        pitch_warnings = [w for w in warnings if "PITCH" in w]
        assert len(pitch_warnings) >= 1
    def test_no_excessive_attitude_clean(self, sample_data):
        """Normal roll/pitch (< 360°) → no warnings."""
        warnings = check_excessive_attitude(sample_data)
        assert warnings == []
    def test_custom_attitude_limits(self, sample_data):
        """Tight limits (5°) catch even mild roll/pitch."""
        warnings = check_excessive_attitude(sample_data, roll_limit=5.0, pitch_limit=5.0)
        assert len(warnings) >= 1
    def test_none_attitude_values(self, empty_data):
        """None roll/pitch entries are skipped."""
        empty_data["attitude"] = [
            {"timestamp": BASE_TS, "roll": None, "pitch": None},
            {"timestamp": BASE_TS + 3, "roll": 0.1, "pitch": None},
        ]
        warnings = check_excessive_attitude(empty_data)
        assert isinstance(warnings, list)
class TestRunAllChecks:
    def test_integration_clean(self, sample_data):
        """Clean flight produces zero or minimal warnings."""
        warnings = run_all_checks(sample_data)
        assert isinstance(warnings, list)
    def test_integration_with_config(self, low_battery_data, sample_config):
        """run_all_checks forwards config thresholds correctly."""
        warnings = run_all_checks(low_battery_data, config=sample_config)
        battery_warnings = [w for w in warnings if "LOW BATTERY" in w]
        assert len(battery_warnings) >= 1
    def test_integration_aggregates(self, empty_data):
        """Combine multiple anomaly types."""
        empty_data["battery"] = [
            {"timestamp": BASE_TS, "battery_remaining": 5, "voltage": 10.0, "current": 5.0},
        ]
        empty_data["position"] = [
            {"timestamp": BASE_TS,     "relative_alt": 50.0},
            {"timestamp": BASE_TS + 3, "relative_alt": 20.0},             
        ]
        empty_data["attitude"] = [
            {"timestamp": BASE_TS, "roll": 7.0, "pitch": 7.0},
        ]
        warnings = run_all_checks(empty_data)
        assert len(warnings) >= 3                                     

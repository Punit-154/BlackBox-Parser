"""Tests for summary.py — flight summary generation."""
from summary import (
    generate_summary,
    _format_duration,
    _haversine,
    _compute_speed_from_position,
)
class TestFormatDuration:
    def test_format_duration_zero(self):
        assert _format_duration(0) == "0m 0s"
        assert _format_duration(-10) == "0m 0s"
    def test_format_duration_minutes(self):
        assert _format_duration(150) == "2m 30s"
    def test_format_duration_hours(self):
        assert _format_duration(3665) == "1h 1m 5s"
class TestHaversine:
    def test_haversine_same_point(self):
        assert _haversine(28.6, 77.2, 28.6, 77.2) == 0.0
    def test_haversine_distance(self):
        dist = _haversine(0.0, 0.0, 1.0, 0.0)
        assert 110000 < dist < 112000
class TestComputeSpeed:
    def test_compute_speed_valid(self):
        pos = [
            {"vx": 3.0, "vy": 4.0},              
            {"vx": -3.0, "vy": -4.0},            
            {"vx": 0.0, "vy": 0.0},              
        ]
        speeds = _compute_speed_from_position(pos)
        assert speeds == [5.0, 5.0, 0.0]
    def test_compute_speed_none_values(self):
        pos = [
            {"vx": 3.0, "vy": 4.0},
            {"vx": None, "vy": 4.0},
            {"vx": 3.0, "vy": None},
            {"vx": None, "vy": None},
        ]
        speeds = _compute_speed_from_position(pos)
        assert speeds == [5.0]
class TestGenerateSummary:
    def test_duration_calculation(self, sample_data):
        stats = generate_summary(sample_data)
        assert stats["duration_seconds"] == 27.0
        assert stats["duration_formatted"] == "0m 27s"
    def test_max_altitude(self, sample_data):
        stats = generate_summary(sample_data)
        assert stats["max_altitude"] == 50.0
    def test_max_altitude_empty(self, empty_data):
        stats = generate_summary(empty_data)
        assert stats["max_altitude"] == 0.0
    def test_speed_from_gps(self, sample_data):
        stats = generate_summary(sample_data)
        assert stats["max_speed"] == 15.0
        assert stats["avg_speed"] > 0.0
    def test_speed_from_position_fallback(self, sample_data):
        for row in sample_data["gps"]:
            row["speed"] = None
        stats = generate_summary(sample_data)
        assert stats["max_speed"] > 0.0
        assert stats["avg_speed"] > 0.0
    def test_battery_stats(self, sample_data):
        stats = generate_summary(sample_data)
        assert stats["battery_start"] == 95
        assert stats["battery_end"] == 85
        assert stats["battery_used"] == 10
    def test_battery_unavailable(self, empty_data):
        stats = generate_summary(empty_data)
        assert stats["battery_start"] == -1
        assert stats["battery_end"] == -1
        assert stats["battery_used"] == 0
    def test_climb_descent_rates(self, altitude_drop_data):
        stats = generate_summary(altitude_drop_data)
        assert stats["peak_descent_rate"] == 5.0
        assert stats["peak_climb_rate"] > 0.0
    def test_events_included(self, sample_data):
        stats = generate_summary(sample_data)
        assert len(stats["events"]) == 2
        assert stats["events"][0]["name"] == "Armed"

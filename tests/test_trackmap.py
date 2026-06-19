"""Tests for trackmap.py GPS flight track visualization."""

import os
import pytest

import trackmap


class TestExtractGpsCoords:
    def test_extracts_from_gps(self, sample_data):
        coords = trackmap._extract_gps_coords(sample_data)
        assert len(coords) == 10
        assert all(len(c) == 2 for c in coords)

    def test_falls_back_to_position(self, empty_data):
        empty_data["position"] = [
            {"lat": 28.0, "lon": 77.0},
            {"lat": 28.1, "lon": 77.1},
        ]
        coords = trackmap._extract_gps_coords(empty_data)
        assert len(coords) == 2

    def test_filters_none_coords(self, empty_data):
        empty_data["gps"] = [
            {"lat": 28.0, "lon": 77.0},
            {"lat": None, "lon": 77.1},
            {"lat": 28.2, "lon": None},
            {"lat": 28.3, "lon": 77.3},
        ]
        coords = trackmap._extract_gps_coords(empty_data)
        assert len(coords) == 2

    def test_empty_data(self, empty_data):
        coords = trackmap._extract_gps_coords(empty_data)
        assert len(coords) == 0


class TestGetCenter:
    def test_center_of_two_points(self):
        coords = [(28.0, 77.0), (28.2, 77.2)]
        center = trackmap._get_center(coords)
        assert center == (28.1, 77.1)

    def test_center_single_point(self):
        coords = [(28.0, 77.0)]
        center = trackmap._get_center(coords)
        assert center == (28.0, 77.0)

    def test_empty_coords(self):
        center = trackmap._get_center([])
        assert center == (0.0, 0.0)


class TestGenerateTrackMap:
    def test_creates_html_file(self, sample_data, tmp_path):
        output_dir = str(tmp_path)
        result = trackmap.generate_track_map(sample_data, output_dir=output_dir)

        assert result is not None
        assert os.path.isfile(result)
        assert result.endswith("flight_track.html")

        size = os.path.getsize(result)
        assert size > 1000

    def test_html_contains_leaflet(self, sample_data, tmp_path):
        result = trackmap.generate_track_map(sample_data, output_dir=str(tmp_path))
        with open(result, "r", encoding="utf-8") as f:
            content = f.read()
        assert "leaflet" in content.lower()
        assert "OpenStreetMap" in content

    def test_empty_data_returns_none(self, empty_data, tmp_path):
        result = trackmap.generate_track_map(empty_data, output_dir=str(tmp_path))
        assert result is None

    def test_single_point_returns_none(self, empty_data, tmp_path):
        empty_data["gps"] = [{"lat": 28.0, "lon": 77.0}]
        result = trackmap.generate_track_map(empty_data, output_dir=str(tmp_path))
        assert result is None

    def test_takes_off_landing_markers(self, sample_data, tmp_path):
        result = trackmap.generate_track_map(sample_data, output_dir=str(tmp_path))
        with open(result, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Takeoff" in content
        assert "Landing" in content

    def test_speed_color_coding(self, sample_data, tmp_path):
        result = trackmap.generate_track_map(sample_data, output_dir=str(tmp_path))
        with open(result, "r", encoding="utf-8") as f:
            content = f.read()
        assert "#4CAF50" in content or "#FFC107" in content or "#FF9800" in content or "#F44336" in content

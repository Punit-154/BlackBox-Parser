"""Tests for exporter.py — CSV export functions."""
import os
from exporter import (
    export_gps_csv,
    export_altitude_csv,
    export_battery_csv,
    export_attitude_csv,
    export_all,
)
class TestExporters:
    def test_export_gps_csv(self, sample_data, tmp_path):
        out_dir = str(tmp_path)
        path = export_gps_csv(sample_data, out_dir)
        assert path is not None
        assert os.path.isfile(path)
        assert path.endswith("gps.csv")
        with open(path, "r") as f:
            lines = f.readlines()
            assert len(lines) == 11                      
    def test_export_gps_empty(self, empty_data, tmp_path):
        path = export_gps_csv(empty_data, str(tmp_path))
        assert path is None
    def test_export_altitude_csv(self, sample_data, tmp_path):
        out_dir = str(tmp_path)
        path = export_altitude_csv(sample_data, out_dir)
        assert path is not None
        assert os.path.isfile(path)
        with open(path, "r") as f:
            header = f.readline()
            assert "ground_speed" in header                  
    def test_export_battery_csv(self, sample_data, tmp_path):
        out_dir = str(tmp_path)
        path = export_battery_csv(sample_data, out_dir)
        assert path is not None
        assert os.path.isfile(path)
    def test_export_attitude_csv(self, sample_data, tmp_path):
        out_dir = str(tmp_path)
        path = export_attitude_csv(sample_data, out_dir)
        assert path is not None
        assert os.path.isfile(path)
        with open(path, "r") as f:
            header = f.readline()
            assert "roll_deg" in header                  
    def test_export_all(self, sample_data, tmp_path):
        out_dir = str(tmp_path)
        paths = export_all(sample_data, output_dir=out_dir)
        assert len(paths) == 4
        for p in paths:
            assert os.path.isfile(p)
    def test_export_creates_dir(self, sample_data, tmp_path):
        out_dir = os.path.join(str(tmp_path), "nested", "csv")
        paths = export_all(sample_data, output_dir=out_dir)
        assert len(paths) == 4
        assert os.path.isdir(out_dir)

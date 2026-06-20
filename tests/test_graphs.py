"""Smoke tests for graphs.py — verify PNG generation works without crashing."""
import os
from graphs import (
    generate_altitude_graph,
    generate_battery_graph,
    generate_speed_graph,
    generate_attitude_graph,
    generate_power_graph,
    generate_all_graphs,
)
class TestGraphGeneration:
    def test_altitude_graph_created(self, sample_data, tmp_path):
        out_dir = str(tmp_path)
        path = generate_altitude_graph(sample_data, out_dir)
        assert path is not None
        assert os.path.isfile(path)
        assert os.path.getsize(path) > 0
    def test_battery_graph_created(self, sample_data, tmp_path):
        out_dir = str(tmp_path)
        path = generate_battery_graph(sample_data, out_dir)
        assert path is not None
        assert os.path.isfile(path)
        assert os.path.getsize(path) > 0
    def test_speed_graph_created(self, sample_data, tmp_path):
        out_dir = str(tmp_path)
        path = generate_speed_graph(sample_data, out_dir)
        assert path is not None
        assert os.path.isfile(path)
        assert os.path.getsize(path) > 0
    def test_attitude_graph_created(self, sample_data, tmp_path):
        out_dir = str(tmp_path)
        path = generate_attitude_graph(sample_data, out_dir)
        assert path is not None
        assert os.path.isfile(path)
        assert os.path.getsize(path) > 0
    def test_power_graph_created(self, sample_data, tmp_path):
        out_dir = str(tmp_path)
        path = generate_power_graph(sample_data, out_dir)
        assert path is not None
        assert os.path.isfile(path)
        assert os.path.getsize(path) > 0
    def test_generate_all_graphs(self, sample_data, tmp_path):
        out_dir = str(tmp_path)
        paths = generate_all_graphs(sample_data, output_dir=out_dir)
        assert len(paths) == 5
        for p in paths:
            assert os.path.isfile(p)
            assert os.path.getsize(p) > 0
    def test_empty_data_handled(self, empty_data, tmp_path):
        out_dir = str(tmp_path)
        paths = generate_all_graphs(empty_data, output_dir=out_dir)
        assert len(paths) == 0

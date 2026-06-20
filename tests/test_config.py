"""Tests for config.py — YAML configuration system."""
import os
import yaml
from config import load_config, DEFAULT_CONFIG
class TestConfigLoader:
    def test_default_config_returned(self):
        """No path given, config.yaml missing -> returns defaults."""
        config = load_config(path="nonexistent_fake_path.yaml")
        assert config == DEFAULT_CONFIG
    def test_load_valid_yaml(self, tmp_path):
        """Loads valid YAML and deep-merges with defaults."""
        user_config = {
            "thresholds": {
                "battery_low_percent": 30,
            },
            "output": {
                "csv_dir": "custom_csv",
            }
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(user_config, f)
        config = load_config(path=str(config_file))
        assert config["thresholds"]["battery_low_percent"] == 30
        assert config["output"]["csv_dir"] == "custom_csv"
        assert config["thresholds"]["altitude_drop_m"] == 10.0
        assert config["output"]["graph_dir"] == "output/graphs"
    def test_invalid_yaml(self, tmp_path):
        """Malformed YAML -> falls back to defaults."""
        config_file = tmp_path / "bad.yaml"
        config_file.write_text("thresholds: [this is invalid yaml\n  - unclosed")
        config = load_config(path=str(config_file))
        assert config == DEFAULT_CONFIG
    def test_not_a_mapping(self, tmp_path):
        """YAML is valid but not a dict (e.g. a list) -> falls back."""
        config_file = tmp_path / "list.yaml"
        config_file.write_text("- item1\n- item2")
        config = load_config(path=str(config_file))
        assert config == DEFAULT_CONFIG
    def test_config_types_preserved(self, tmp_path):
        """Values retain their types after merge."""
        user_config = {
            "thresholds": {"altitude_drop_m": 15},                       
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(user_config, f)
        config = load_config(path=str(config_file))
        assert isinstance(config["thresholds"]["altitude_drop_m"], int)
        assert config["thresholds"]["altitude_drop_m"] == 15

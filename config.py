"""Configuration loader for BlackBox-Parser.
Provides a default configuration dictionary and a ``load_config()``
function that optionally reads overrides from a YAML file, deep-merging
them with the defaults so that every key is always present.
"""
import copy
import os
import yaml
DEFAULT_CONFIG = {
    "thresholds": {
        "battery_low_percent": 20,
        "altitude_drop_m": 10.0,
        "roll_limit_deg": 360.0,
        "pitch_limit_deg": 360.0,
    },
    "output": {
        "csv_dir": "output/csv",
        "graph_dir": "output/graphs",
    },
    "battery_estimation": {
        "cell_voltage_full": 4.2,
        "cell_voltage_empty": 3.5,
    },
}
def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into a copy of *base*.
    - Keys present only in *base* are preserved (defaults).
    - Keys present only in *override* are added.
    - For keys present in both: if both values are dicts the merge
      recurses; otherwise the *override* value wins.
    Returns a new dict — neither *base* nor *override* is mutated.
    """
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged
def load_config(path=None) -> dict:
    """Load configuration, optionally overriding defaults from a YAML file.
    Parameters
    ----------
    path : str or None
        Path to a YAML configuration file.
        - If *None* (default), the function looks for ``config.yaml`` in
          the current working directory.  If that file does not exist the
          built-in defaults are returned silently.
        - If a path is given explicitly but the file cannot be read or
          parsed, a warning is printed and the built-in defaults are
          returned.
    Returns
    -------
    dict
        The merged configuration dictionary.  Every key defined in
        ``DEFAULT_CONFIG`` is guaranteed to be present.
    """
    explicit = path is not None
    if path is None:
        path = os.path.join(os.getcwd(), "config.yaml")
    if not os.path.isfile(path):
        if explicit:
            print(f"[WARN] Config file not found: {path} — using defaults.")
        return copy.deepcopy(DEFAULT_CONFIG)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            user_cfg = yaml.safe_load(fh)
    except Exception as exc:
        if explicit:
            print(f"[WARN] Failed to read config file: {exc} — using defaults.")
        return copy.deepcopy(DEFAULT_CONFIG)
    if not isinstance(user_cfg, dict):
        if explicit:
            print("[WARN] Config file did not contain a YAML mapping — using defaults.")
        return copy.deepcopy(DEFAULT_CONFIG)
    return _deep_merge(DEFAULT_CONFIG, user_cfg)

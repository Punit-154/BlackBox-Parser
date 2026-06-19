# config.py + config.yaml — Configuration System

## What It Does
Provides a default configuration and allows users to override any value via a YAML file.

## Files
- `config.py` — Python module with defaults and loader
- `config.yaml` — User-editable config file

## Default Configuration (hardcoded in config.py)
```python
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
```

## How It Works

### load_config(path=None) → dict
1. If no path given, looks for `config.yaml` in current directory
2. If file doesn't exist → returns deep copy of defaults (silent)
3. If file exists → reads YAML, deep-merges with defaults
4. Returns merged config (every default key is always present)

### _deep_merge(base, override) → dict
Recursively merges override into base:
- Dicts merge recursively
- Non-dict values: override wins
- Returns NEW dict (never mutates inputs)

## config.yaml Sections

### thresholds
Control anomaly detection sensitivity:
```yaml
thresholds:
  battery_low_percent: 20    # Warn when battery < 20%
  altitude_drop_m: 10.0      # Warn on >10m sudden drop
  roll_limit_deg: 360.0      # 360 = disabled
  pitch_limit_deg: 360.0     # 360 = disabled
```

### output
Control where files are saved:
```yaml
output:
  csv_dir: "output/csv"
  graph_dir: "output/graphs"
```

### battery_estimation
For .bin logs that lack battery percentage:
```yaml
battery_estimation:
  cell_voltage_full: 4.2    # Fully charged LiPo cell
  cell_voltage_empty: 3.5   # Empty LiPo cell
```

## Who Uses the Config
- `analyzer.py` — reads output directories
- `parser.py` — reads battery estimation params for .bin logs
- `anomalies.py` — reads threshold values

## Interview Points
- Deep merge pattern — user overrides only what they want, everything else keeps defaults
- `copy.deepcopy()` — prevents accidental mutation of DEFAULT_CONFIG
- YAML chosen over JSON for human-readability (comments, no quotes needed)
- Config is loaded ONCE in `main()` and passed to all modules — single source of truth

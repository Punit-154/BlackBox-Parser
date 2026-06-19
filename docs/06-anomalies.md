# anomalies.py — Anomaly Detection Module

## What It Does
Scans parsed telemetry data for dangerous conditions and generates warning messages.

## File Location
`anomalies.py` (project root)

## Default Thresholds
| Check | Default Threshold | Configurable Via |
|-------|------------------|-----------------|
| Low battery | 20% | `config.yaml → thresholds.battery_low_percent` |
| Altitude drop | 10.0 m | `config.yaml → thresholds.altitude_drop_m` |
| Excessive roll | 360° (disabled) | `config.yaml → thresholds.roll_limit_deg` |
| Excessive pitch | 360° (disabled) | `config.yaml → thresholds.pitch_limit_deg` |

Note: Roll and pitch limits default to 360° which effectively disables them. Set to realistic values (e.g., 45°) in `config.yaml` to enable.

## Key Functions

### check_low_battery(data, threshold) → list[str]
- Iterates through `data["battery"]`
- Skips entries where `battery_remaining` is `None` (common in .bin logs)
- Triggers when battery drops below threshold
- Only warns ONCE (first occurrence) to avoid spam
- Returns list like: `["! LOW BATTERY: Battery dropped below 20% (was 18%) at 22:13:25"]`

### check_altitude_drop(data, threshold) → list[str]
- Filters to records with valid `relative_alt`
- Compares consecutive altitude readings
- Triggers when `prev_alt - curr_alt >= threshold`
- Can warn MULTIPLE times (each drop event)
- Returns: `["! ALTITUDE DROP: Sudden drop of 15.0 m detected at 22:13:29 (55.0 m -> 40.0 m)"]`

### check_excessive_attitude(data, roll_limit, pitch_limit) → list[str]
- Converts roll/pitch from radians to degrees
- Triggers when absolute angle exceeds limit
- Checks both roll AND pitch independently
- Returns warnings for each violation

### run_all_checks(data, config) → list[str]
Master function that:
1. Extracts thresholds from config (if provided)
2. Calls all three check functions
3. Returns combined warning list

### print_warnings(warning_list)
Prints formatted output:
```
=============================================
            FLIGHT WARNINGS
=============================================
  Found 2 warning(s):
  1. ! LOW BATTERY: ...
  2. ! ALTITUDE DROP: ...

=============================================
```

## Why This Matters for Drones
- **Low battery**: Drone may fall out of sky
- **Altitude drop**: Could indicate motor failure, prop damage, or wind gust
- **Excessive roll/pitch**: Drone is unstable, may be crashing

## Interview Points
- Single-warn pattern for battery (avoids flooding output with 100 "low battery" lines)
- None-safe filtering throughout — critical for .bin logs where fields are missing
- Configurable thresholds — different drones/missions have different safety margins
- Returns list of strings rather than printing directly — enables testing and programmatic use

# summary.py — Flight Summary Generator

## What It Does
Takes the parsed data dict and computes key flight statistics, then prints a formatted summary to the terminal.

## File Location
`summary.py` (project root)

## Key Functions

### generate_summary(data) → dict
Computes and returns a dictionary of flight statistics:

| Statistic | How It's Calculated |
|-----------|-------------------|
| `duration_seconds` | `end_time - start_time` from meta |
| `max_altitude` | `max()` of all `relative_alt` values (filters None) |
| `avg_speed` / `max_speed` | From GPS speed, or computed from `sqrt(vx² + vy²)` if GPS unavailable |
| `total_distance` | Sum of Haversine distances between consecutive GPS points |
| `max_displacement` | Max Haversine distance from takeoff point to any GPS point |
| `peak_climb_rate` | Max positive `dz/dt` between consecutive position entries |
| `peak_descent_rate` | Max negative `dz/dt` (displayed as positive) |
| `battery_start` / `battery_end` / `battery_used` | First and last `battery_remaining` values |
| `events` | Chronologically sorted flight events |

### print_summary(stats)
Prints the formatted table to terminal with labels like:
```
============================================
              FLIGHT SUMMARY
============================================
  Duration           : 5m 30s
  Max Altitude       : 50.0 m
  ...
```

### _haversine(lat1, lon1, lat2, lon2) → float
Calculates great-circle distance between two GPS coordinates using the **Haversine formula**. Accounts for Earth's curvature — cannot use flat geometry for GPS coordinates.

### _format_duration(seconds) → str
Converts seconds to human-readable format: `"5m 30s"` or `"1h 15m 30s"`.

## Interview Points
- Haversine formula: `a = sin²(Δφ/2) + cos(φ1)·cos(φ2)·sin²(Δλ/2)`, `c = 2·atan2(√a, √(1-a))`, `d = R·c`
- Discrete derivative for climb/descent rate: `rate = (alt2 - alt1) / (time2 - time1)`
- Graceful degradation: if GPS speed unavailable, falls back to position velocity components
- Filters `None` values everywhere — critical for .bin logs that have incomplete data

# graphs.py — Visualization Module

## What It Does
Generates PNG graph images from parsed telemetry data using matplotlib.

## File Location
`graphs.py` (project root)

## Output Files
| Graph | Data Source | What It Shows |
|-------|-----------|---------------|
| `altitude_vs_time.png` | position data | Drone height over time with filled area |
| `battery_vs_time.png` | battery data | Battery percentage drain curve |
| `speed_vs_time.png` | GPS or position data | Ground speed over time |
| `attitude_vs_time.png` | attitude data | Roll (blue) and pitch (red) angles over time |
| `power_vs_time.png` | battery data | Voltage (blue, left axis) and current (red, right axis) |

## Key Design Decisions

### matplotlib.use("Agg")
Line 5 sets the backend to "Agg" — a non-interactive renderer. This is REQUIRED because the tool runs on servers/terminals where no display is available. Without this, matplotlib would crash trying to open a GUI window.

### Dual-axis graph (power_vs_time)
Uses `ax1.twinx()` to create a second Y-axis. Voltage and current have different scales, so plotting them on the same axis would make one invisible.

## Key Functions

### generate_all_graphs(data, output_dir) → list[str]
Master function that calls all five graph generators.

### generate_altitude_graph(data, output_dir)
- Filters records with valid `relative_alt`
- Plots time (x) vs altitude (y) with blue fill
- Converts Unix timestamps to datetime objects for x-axis formatting

### generate_battery_graph(data, output_dir)
- Filters out `None` and negative `battery_remaining` values
- Sets y-axis limit to 0-105% for consistent scaling

### generate_speed_graph(data, output_dir)
- **Prefers GPS data** (direct speed field)
- **Falls back to position data** — computes `sqrt(vx² + vy²)` if GPS speed unavailable
- Labels which source was used in the legend

### generate_attitude_graph(data, output_dir)
- Converts radians to degrees with `math.degrees()`
- Two lines: roll (blue) and pitch (red)

### generate_power_graph(data, output_dir)
- Dual Y-axis: voltage (left, blue) and current (right, red)
- Combines legends from both axes

## Helper Functions

### _timestamps_to_datetimes(records)
Converts Unix timestamps to Python `datetime` objects. Skips boot-relative timestamps (DataFlash .bin logs) by checking `< 946684800` (year 2000).

### _filter_valid_records(records, field)
Returns only records where the specified field is not `None`.

### _apply_style(ax, title, xlabel, ylabel)
Applies consistent formatting: bold title, grid lines, rotated x-axis labels, HH:MM:SS time format.

## Interview Points
- "Agg" backend enables headless rendering — no GUI needed
- `fig.savefig(filepath, dpi=150)` — 150 DPI for good quality without huge file sizes
- `plt.close(fig)` after each save prevents memory leaks when generating multiple graphs
- `tight_layout()` prevents label clipping
- Dual-axis pattern with `twinx()` for variables with different scales

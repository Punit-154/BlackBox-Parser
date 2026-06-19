# exporter.py — CSV Export Module

## What It Does
Exports parsed telemetry data into CSV files that can be opened in Excel, Google Sheets, or any data analysis tool.

## File Location
`exporter.py` (project root)

## Output Files
| CSV File | Data Source | Contents |
|----------|-----------|---------|
| `output/csv/gps.csv` | `data["gps"]` | lat, lon, alt, speed, satellites, fix_type |
| `output/csv/altitude.csv` | `data["position"]` | lat, lon, alt, relative_alt, ground_speed, heading |
| `output/csv/battery.csv` | `data["battery"]` | voltage, current, battery_remaining |
| `output/csv/attitude.csv` | `data["attitude"]` | roll, pitch, yaw (both radians and degrees), angular rates |

## Key Functions

### export_all(data, output_dir) → list[str]
Master function that calls all four exporters. Returns list of generated file paths.

### export_gps_csv(data, output_dir) → str | None
- Creates DataFrame from `data["gps"]`
- Selects columns in a specific order
- Saves to `gps.csv`
- Returns filepath or `None` if no data

### export_altitude_csv(data, output_dir) → str | None
- Creates DataFrame from `data["position"]`
- **Computes `ground_speed`** from `vx` and `vy` using `sqrt(vx² + vy²)`
- Handles `None` values in vx/vy with `pd.to_numeric(errors="coerce")`

### export_battery_csv(data, output_dir) → str | None
- Exports voltage, current, battery_remaining
- Handles `None` battery_remaining (common in .bin logs)

### export_attitude_csv(data, output_dir) → str | None
- Converts radians to degrees using `math.degrees()`
- Creates additional columns: `roll_deg`, `pitch_deg`, `yaw_deg`
- Handles `None` angular rates (not available in .bin logs)

## Helper
### _ensure_dir(dirpath)
Creates output directory if it doesn't exist (`os.makedirs(..., exist_ok=True)`).

## Interview Points
- Uses pandas for DataFrame operations — efficient column selection and CSV writing
- `exist_ok=True` prevents errors on repeated runs
- Column selection with list comprehension filters out columns that may not exist in the DataFrame
- Ground speed computation from velocity components: `speed = √(vx² + vy²)`

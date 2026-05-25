# MAVLink Flight Log Analyzer (CLI)

A command-line telemetry analysis tool for UAV/drone flight logs using the MAVLink protocol. Parses `.tlog` MAVLink logs, extracts telemetry data, generates flight summaries, exports structured CSV files, generates telemetry graphs, and detects flight anomalies.

---

## Features

- **MAVLink Log Parsing** – Parse `.tlog` files using `pymavlink`
- **Flight Summary** – Duration, altitude, speed, battery, and sample counts
- **CSV Export** – GPS, altitude, battery, and attitude data as CSV files
- **Graph Generation** – Altitude, battery, speed, and attitude plots saved as PNG
- **Anomaly Detection** – Low battery, sudden altitude drops, excessive roll/pitch

---

## Project Structure

```
mavlink-analyzer/
│
├── analyzer.py          # Main CLI entry point (argparse)
├── parser.py            # MAVLink .tlog file parser
├── summary.py           # Flight summary computation & display
├── exporter.py          # CSV export module (pandas)
├── graphs.py            # Matplotlib graph generation
├── anomalies.py         # Anomaly / warning detection
├── requirements.txt     # Python dependencies
├── README.md            # This file
│
├── logs/                # Place your .tlog files here
│   └── sample.tlog
│
└── output/              # Generated output files
    ├── csv/             # Exported CSV files
    │   ├── gps.csv
    │   ├── altitude.csv
    │   ├── battery.csv
    │   └── attitude.csv
    └── graphs/          # Generated PNG graphs
        ├── altitude_vs_time.png
        ├── attitude_vs_time.png
        ├── battery_vs_time.png
        └── speed_vs_time.png
```

---

## Setup

### Prerequisites

- Python 3.10 or later
- pip

### Installation

```bash
# 1. Clone or download the project
cd mavlink-analyzer

# 2. (Recommended) Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Usage

Place your `.tlog` MAVLink log file in the `logs/` directory (or provide a path).

### CLI Commands

```bash
# Print flight summary
python analyzer.py logs/sample.tlog --summary

# Export telemetry to CSV
python analyzer.py logs/sample.tlog --export

# Generate graphs
python analyzer.py logs/sample.tlog --graphs

# Run anomaly detection
python analyzer.py logs/sample.tlog --warnings

# Run ALL analysis steps at once
python analyzer.py logs/sample.tlog --all
```

You can combine flags:

```bash
python analyzer.py logs/sample.tlog --summary --warnings
python analyzer.py logs/sample.tlog --export --graphs
```

---

## Example Output

### Flight Summary (`--summary`)

```
==============================================
|   MAVLink Flight Log Analyzer (CLI)        |
|   Parse - Summarise - Export - Visualise   |
==============================================

[INFO] Parsing log file: sample.tlog
[INFO] Parsed 14832 relevant messages out of 52140 total.

=============================================
              FLIGHT SUMMARY
=============================================

  Duration           : 12m 21s
  Total Messages     : 52140
  Parsed Messages    : 14832

  Max Altitude       : 121.4 m
  Average Speed      : 10.83 m/s
  Max Speed          : 18.24 m/s

  Battery Start      : 98%
  Battery End        : 82%
  Battery Used       : 16%

  GPS Samples        : 7416
  Attitude Samples   : 3708

=============================================
```

### CSV Export (`--export`)

```
[INFO] Exporting CSV files to: output/csv/
[OK] Exported GPS data        -> output/csv/gps.csv        (3708 rows)
[OK] Exported Altitude data   -> output/csv/altitude.csv   (3708 rows)
[OK] Exported Battery data    -> output/csv/battery.csv    (3708 rows)
[OK] Exported Attitude data   -> output/csv/attitude.csv   (3708 rows)
[INFO] Exported 4 CSV file(s).
```

### Graph Generation (`--graphs`)

```
[INFO] Generating graphs in: output/graphs/
[OK] Graph saved -> output/graphs/altitude_vs_time.png
[OK] Graph saved -> output/graphs/attitude_vs_time.png
[OK] Graph saved -> output/graphs/battery_vs_time.png
[OK] Graph saved -> output/graphs/speed_vs_time.png
[INFO] Generated 4 graph(s).
```

### Anomaly Detection (`--warnings`)

```
=============================================
            FLIGHT WARNINGS
=============================================

  Found 3 warning(s):

  1. ! LOW BATTERY: Battery dropped below 20% (was 18%) at 14:32:15
  2. ! ALTITUDE DROP: Sudden drop of 12.3 m detected at 14:28:41 (85.2 m -> 72.9 m)
  3. ! EXCESSIVE ROLL: Roll angle of 52.4 degrees exceeds limit of 45 degrees at 14:29:03

=============================================
```

---

## Supported MAVLink Messages

| Message Type           | Data Extracted                                    |
|------------------------|---------------------------------------------------|
| `GPS_RAW_INT`          | Latitude, longitude, altitude, speed, satellites  |
| `GLOBAL_POSITION_INT`  | Lat, lon, MSL & relative alt, velocity, heading   |
| `SYS_STATUS`           | Battery voltage, current, remaining percentage    |
| `ATTITUDE`             | Roll, pitch, yaw (radians), angular velocities    |

---

## Warning Thresholds

| Check                | Default Threshold | Description                          |
|----------------------|-------------------|--------------------------------------|
| Low Battery          | < 20%             | Battery remaining below threshold    |
| Altitude Drop        | > 10 m            | Drop between consecutive samples     |
| Excessive Roll/Pitch | > 45°             | Absolute roll or pitch angle         |

Thresholds can be modified in `anomalies.py` at the top of the file.

---

## Dependencies

| Package      | Purpose                              |
|--------------|--------------------------------------|
| `pymavlink`  | Parse MAVLink binary `.tlog` files   |
| `pandas`     | Structured data handling & CSV I/O   |
| `matplotlib` | Generate telemetry time-series plots |

---

## Notes

- This is a **CLI-only** tool – no web dashboard or GUI.
- No machine learning or real-time telemetry processing.
- Designed to be beginner-friendly and easy to extend.
- Works with standard ArduPilot / PX4 `.tlog` files generated by Mission Planner, QGroundControl, or MAVProxy.

---


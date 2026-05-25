# MAVLink Flight Log Analyzer

A modular command-line tool for parsing and analyzing flight logs.
It fully supports both:
- MAVLink telemetry logs (`.tlog`)
- ArduPilot DataFlash binary logs (`.bin`)

## Features
- **Format Auto-Detection**: Automatically parses `.tlog` and `.bin` logs into a unified internal data schema.
- **Summary**: Generates an overview of flight duration, speed, max altitude, battery usage, and more.
- **CSV Export**: Extracts telemetry into `output/csv/` for GPS, Attitude, Altitude, and Battery data.
- **Graphs**: Generates PNG visualizations in `output/graphs/` for Altitude, Battery, Speed, and Attitude vs. Time.
- **Anomalies**: Detects critical warnings (low battery, altitude drop, excessive roll/pitch angles).

## Installation

```bash
# Create a virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate  # On Windows

# Install requirements
pip install -r requirements.txt
```

## Usage

```bash
# View help
python analyzer.py --help

# Run specific analyses on a .tlog or .bin file
python analyzer.py logs/sample.tlog --summary
python analyzer.py logs/sample.bin --export --graphs

# Run all analysis steps at once (summary, export, graphs, warnings)
python analyzer.py logs/sample.tlog --all
```

## Architecture Notes
The project is built on a "schema normalization" approach:
- `parser.py` maps the different raw messages from `.tlog` (`GPS_RAW_INT`, `ATTITUDE`, etc.) and `.bin` (`GPS`, `ATT`, etc.) into a **common internal data structure** using human-readable units (meters, degrees, m/s, volts).
- Missing data fields in `.bin` files (such as `battery_remaining`, `vx`, `vy`, `vz`, `relative_alt`) are safely filtered out, handled as `None`, or skipped in the downstream analyzer modules (`summary.py`, `graphs.py`, `anomalies.py`, `exporter.py`) to prevent errors and ensure backward compatibility.

# Project Roadmap: MAVLink Flight Log Analyzer

## Phase 1 — Foundation (DONE)
- [x] Parse MAVLink `.tlog` telemetry logs
- [x] Parse ArduPilot DataFlash `.bin` binary logs
- [x] Schema normalization (common internal data structure)
- [x] Flight summary (duration, altitude, speed, battery, distance, climb/descent)
- [x] CSV export (GPS, altitude, battery, attitude)
- [x] PNG graph generation (altitude, battery, speed, power, attitude)
- [x] Anomaly detection (low battery, altitude drop, excessive roll/pitch)
- [x] YAML-based configuration with defaults
- [x] Unit tests with pytest (79 tests, 100% pass)

## Phase 2 — UX Improvements (DONE)
- [x] Interactive menu mode (`--interactive`)
- [x] Multi-choice input support (`1,3` or `2 4`)
- [x] Hot-swap log file without restarting (option 8)
- [x] PDF report generation (`--report`) — single-file shareable report with embedded graphs
- [x] Batch mode (`--batch folder/`) — analyze multiple logs, comparison table
- [x] Flight track map (`--map`) — interactive HTML map with color-coded path

## Phase 3 — Next Steps (FUTURE)
- [ ] **Live streaming** — read from serial port or UDP for real-time analysis
- [ ] **JSON output** — machine-readable output for dashboard integration
- [ ] **Plugin system** — user-defined anomaly checks via Python scripts
- [ ] **More formats** — DJI CSV, Betaflight Blackbox, PX4 `.ulg`

## Phase 4 — Distribution (FUTURE)
- [ ] Publish to PyPI (`pip install mavlink-flight-log-analyzer`)
- [ ] GitHub Releases with zip downloads
- [ ] Dockerfile for containerized usage
- [ ] Homebrew formula for macOS/Linux

## How to Read This Roadmap
Each phase builds on the previous. Phase 1-2 are complete. Phase 3 adds features that make the tool more powerful. Phase 4 makes it easy for others to install and use.

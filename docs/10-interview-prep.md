# Interview Preparation Guide

## Project Overview (30-second pitch)
"I built a Python CLI tool that analyzes drone flight logs. It supports two formats — MAVLink .tlog and ArduPilot .bin — auto-detects the format, normalizes the data into a common schema, and provides five analysis modes: summary, CSV export, graph generation, anomaly detection, and PDF report generation. It has an interactive menu mode, YAML-based configuration, and 89 passing tests."

## Key Technical Concepts to Mention

### 1. Schema Normalization
"I created a common internal data structure that both .tlog and .bin parsers produce. This means all downstream modules — summary, export, graphs, anomalies — work identically regardless of the input format. Adding a new format just requires a new parser, not changes to existing code."

### 2. Haversine Formula
"For calculating flight distance and displacement, I used the Haversine formula because GPS coordinates are on a sphere, not a flat plane. Simple Euclidean distance would be inaccurate for flights covering significant distances."

### 3. Defensive Programming
"Every module checks for `None` values because .bin logs are missing several fields that .tlog logs have. The tool never crashes on incomplete data — it just skips what's unavailable."

### 4. Configuration System
"I implemented a YAML-based config with deep-merge. Users can override any default value without specifying everything. The config is loaded once and passed to all modules — no global state."

### 5. Interactive Mode
"I added a menu-driven interface that accepts single or multiple selections (e.g., '1,3' to run summary and export). It supports hot-swapping log files without restarting."

### 6. PDF Report Generation
"I created a self-contained PDF report that combines flight summary, embedded graphs, and anomaly warnings into a single shareable file. The report uses a custom FPDF subclass with header/footer, and graphs are generated in a temporary directory then embedded as images."

## Common Interview Questions & Answers

### Q: What was the hardest part?
"The .bin format. DataFlash logs are missing fields that .tlog has — no relative altitude, no battery percentage, no velocity components. I had to reconstruct relative altitude from GPS data and estimate battery percentage from voltage using LiPo cell characteristics."

### Q: How did you handle errors?
"Every function that reads from the data dict checks for None. Parser validation catches wrong file types and missing files. The CLI has proper exit codes (0 for success, 1 for errors). Tests cover both success and failure paths."

### Q: Why not use an existing library?
"pymavlink handles the low-level protocol parsing, but no library provides the full analysis pipeline — summary, export, graphs, and anomaly detection in one tool. I built the analysis layer on top of pymavlink."

### Q: How would you scale this?
"Three areas: batch mode for analyzing folders of logs, live streaming from serial/UDP for real-time analysis, and a web dashboard using the JSON output mode I'd add."

### Q: What would you do differently?
"Start with type hints from day one. Add logging instead of print statements. Use a proper CLI framework like Click instead of argparse for better UX."

## Code Walkthrough (be ready to explain)

1. **Entry point** → `analyzer.py:main()` — parses args, loads config, routes to interactive or flag mode
2. **Parsing** → `parser.py:parse_log()` — auto-detects format, dispatches to parser
3. **Normalization** → `_PARSERS` dict maps message types to handler functions
4. **Post-processing** → `_post_process_bin_data()` reconstructs missing .bin fields
5. **Summary** → `summary.py:generate_summary()` — Haversine for distance, discrete derivative for climb rate
6. **Export** → `exporter.py` — pandas DataFrames to CSV
7. **Graphs** → `graphs.py` — matplotlib with Agg backend, dual-axis for power
8. **Anomalies** → `anomalies.py` — threshold-based checks with None-safe filtering
9. **PDF Report** → `reporter.py` — FPDF subclass, temp directory for graphs, embedded images

## Numbers to Remember
- 89 tests, 100% pass rate
- 2 log formats supported (.tlog, .bin)
- 5 MAVLink message types parsed
- 6 DataFlash message types parsed
- 5 graph types generated
- 4 CSV files exported
- 3 anomaly checks implemented
- 1 PDF report with embedded graphs

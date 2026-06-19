# reporter.py — PDF Report Generator

## What It Does
Generates a self-contained PDF report that combines flight summary, embedded graphs, and anomaly warnings into a single shareable file.

## File Location
`reporter.py` (project root)

## Output
`output/flight_report.pdf` — a multi-page PDF with:
1. Title page (log filename, generation timestamp)
2. Flight summary statistics
3. Embedded telemetry graphs (altitude, battery, speed, attitude, power)
4. Anomaly detection warnings

## Key Components

### FlightReport(FPDF)
Custom class extending `fpdf.FPDF` with project-specific layout:

| Method | Purpose |
|--------|---------|
| `header()` | Adds header to every page with log filename |
| `footer()` | Adds page numbers (Page X/Y) |
| `add_title_page()` | Cover page with title, filename, timestamp |
| `add_summary_section(stats)` | Renders flight statistics in key-value format |
| `add_graphs_section(graph_paths)` | Embeds PNG images into the PDF |
| `add_warnings_section(warnings)` | Lists warnings in red text |

### generate_report(data, output_dir, config) → str | None
Master function that:
1. Generates summary stats from data
2. Runs anomaly checks
3. Generates all 5 graph types into a temporary directory
4. Creates PDF with title, summary, graphs, and warnings
5. Saves to `output/flight_report.pdf`

## How Graphs Are Embedded
Graphs are generated as PNG files into a `tempfile.TemporaryDirectory()`, then embedded into the PDF using `pdf.image(path, x=10, w=190)`. The temp directory is automatically cleaned up after the PDF is saved.

## PDF Structure
```
Page 1: Title Page
  - "Flight Analysis Report" (blue, large)
  - Log filename
  - Generation timestamp
  - Feature list

Page 2+: Summary Section
  - Flight duration, message counts
  - Telemetry: altitude, speed, distance, climb rates
  - Battery: start, end, used percentages
  - GPS and attitude sample counts
  - Flight events timeline (if any)

Page N+: Graphs Section
  - Each graph gets its own space
  - Auto page break when near bottom
  - Graph label above each image

Page M: Warnings Section
  - "No warnings" in green (if clean)
  - Numbered list of warnings in red (if any)
```

## Dependencies
- `fpdf2` — lightweight PDF generation library
- `matplotlib` — for generating the graph PNGs
- `tempfile` — for temporary graph storage

## Why fpdf2 Over Alternatives
| Library | Pros | Cons |
|---------|------|------|
| `fpdf2` | Pure Python, no system deps, simple API | Limited font support (no Unicode with default fonts) |
| `reportlab` | Powerful, full Unicode | Complex API, larger footprint |
| `weasyprint` | HTML-to-PDF, full CSS | Requires system libraries (Cairo, Pango) |

Chose `fpdf2` for simplicity — no external system dependencies needed.

## Usage
```bash
# Flag-based
python analyzer.py logs/sample.tlog --report

# Interactive mode (option 6)
python analyzer.py --interactive
# Then select: 6
```

## Interview Points
- Subclass pattern: `FlightReport(FPDF)` extends base class with custom header/footer
- Temporary directory pattern: graphs generated in temp dir, embedded, then auto-cleaned
- Single responsibility: `generate_report()` orchestrates, `FlightReport` handles layout
- The PDF is self-contained — all graphs are embedded as images, no external file references

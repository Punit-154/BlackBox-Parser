# Overall Architecture

## System Diagram
```
                    ┌──────────────┐
                    │  analyzer.py │  ← Entry point (CLI)
                    │  (main())    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼────┐ ┌────▼────┐ ┌────▼────┐
         │ parser  │ │ config  │ │         │
         │  .py    │ │  .py    │ │         │
         └────┬────┘ └────┬────┘ │         │
              │            │      │         │
              ▼            ▼      │         │
        ┌─────────────────────┐   │         │
        │   data dict (std)   │◄──┘         │
        └─────────┬───────────┘             │
                  │                         │
     ┌────────────┼────────────┐            │
     │            │            │            │
┌────▼────┐ ┌────▼────┐ ┌────▼────┐ ┌─────▼─────┐ ┌─────────┐
│summary  │ │exporter │ │ graphs  │ │ anomalies │ │reporter │
│  .py    │ │  .py    │ │  .py    │ │   .py     │ │  .py    │
└────┬────┘ └────┬────┘ └────┬────┘ └─────┬─────┘ └────┬────┘
     │            │            │            │             │
     ▼            ▼            ▼            ▼             ▼
  Terminal     CSV files    PNG files   Warnings    PDF report
```

## Core Design Pattern: Schema Normalization
The key architectural decision is the **common data schema**. Every downstream module reads from the same dict structure regardless of whether the input was `.tlog` or `.bin`.

This means:
- `summary.py` doesn't know about MAVLink or DataFlash
- `graphs.py` doesn't know about unit conversions
- `anomalies.py` just checks values in the dict

Each module is **independent** and **testable in isolation**.

## Module Responsibilities

| Module | Input | Output | Responsibility |
|--------|-------|--------|---------------|
| `config.py` | YAML file or defaults | config dict | Configuration management |
| `parser.py` | .tlog or .bin file | data dict | Format detection + parsing |
| `summary.py` | data dict | stats dict + terminal print | Compute flight statistics |
| `exporter.py` | data dict | CSV files | Data export |
| `graphs.py` | data dict | PNG files | Visualization |
| `anomalies.py` | data dict | warning list | Safety checks |
| `reporter.py` | data dict | PDF file | Self-contained report generation |
| `analyzer.py` | CLI args | orchestrates everything | Entry point + routing |

## Data Flow
```
1. User runs: python analyzer.py flight.tlog --all
2. config.py loads config.yaml (or defaults)
3. parser.py reads flight.tlog → produces data dict
4. analyzer.py calls each module with data dict:
   - summary.py → prints to terminal
   - exporter.py → writes CSV files
   - graphs.py → writes PNG files
   - anomalies.py → prints warnings
   - reporter.py → writes PDF report
```

## Key Design Decisions

### 1. Config passed as dict, not imported
Config is loaded once in `main()` and passed to modules that need it. This avoids global state and makes testing easier.

### 2. None-safe everywhere
Every function that reads from the data dict checks for `None` values. This is critical because:
- .bin logs have missing fields
- Users may provide incomplete logs
- The tool should NEVER crash on valid-but-incomplete data

### 3. Functions return data, don't print directly
`generate_summary()` returns a dict. `print_summary()` prints it. This separation allows:
- Testing the computation independently
- Future use (e.g., returning JSON instead of printing)

### 4. Dispatch tables over if/elif
Parser uses `_PARSERS` dict to map message types to handler functions. Adding a new message type = adding one entry to the dict.

## Interview Points
- "Separation of concerns" — each module does ONE thing
- "Schema normalization" — different inputs, same internal representation
- "Dependency injection" — config is passed in, not imported globally
- "Defensive programming" — None checks prevent crashes on edge cases
- "Open for extension, closed for modification" — adding a new log format means adding a new parser, not changing existing ones

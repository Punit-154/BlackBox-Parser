# analyzer.py — The Main Entry Point

## What It Does
This is the **brain** of the CLI. It decides HOW the program runs — either as a flag-based command or as an interactive menu.

## File Location
`analyzer.py` (project root)

## Key Components

### 1. MENU_OPTIONS (dict)
```python
MENU_OPTIONS = {
    "1": "Flight Summary",
    "2": "Export to CSV",
    "3": "Generate Graphs",
    "4": "Anomaly Warnings",
    "5": "Run All Analysis",
    "6": "Generate PDF Report",
    "7": "Change Log File",
    "8": "Batch Analyze Folder",
    "9": "Quit",
}
```
Single source of truth for the interactive menu. If you want to add a new option, update this dict and add a handler in `run_interactive()`.

### 2. build_arg_parser()
Defines all CLI arguments using Python's `argparse` module:
- `logfile` (positional, optional with `nargs="?"`) — path to the log file
- `--summary` — show flight summary
- `--export` — export CSVs
- `--graphs` — generate PNG graphs
- `--warnings` — run anomaly checks
- `--all` — run all of the above
- `--report` — generate self-contained PDF report
- `--batch FOLDER` — analyze all logs in a folder, print comparison table
- `--config` — custom YAML config path
- `--interactive` — launch menu mode

### 3. print_banner()
Prints the ASCII art header. Called once at startup.

### 4. Interactive Mode Functions

| Function | Purpose |
|----------|---------|
| `print_menu()` | Renders the numbered menu from `MENU_OPTIONS` |
| `get_log_file_interactive()` | Prompts user for a file path, validates it exists and has correct extension |
| `load_log_interactive()` | Calls `parse_log()` with error handling, returns `None` on failure |
| `run_interactive()` | The main event loop — shows menu, reads choice(s), dispatches to analysis functions |

**Multi-choice support:** Users can type `1,3` or `2 4` to run multiple analyses in one selection. Safety guards prevent mixing `7` (change file) or `9` (quit) with analysis options.

### 5. Batch Mode Functions

| Function | Purpose |
|----------|---------|
| `find_log_files(folder)` | Finds all .tlog and .bin files in a folder using glob patterns |
| `run_batch(folder, config)` | Processes each log, collects stats, prints comparison table |
| `_print_batch_table(results)` | Formats and prints the side-by-side comparison table |

### 6. main()
The entry point. Flow:
```
1. Parse args with argparse
2. Load config (from --config or default config.yaml)
3. If --batch → call run_batch() → return
4. If --interactive → call run_interactive() → return
5. Otherwise → validate flags, parse log, run selected analyses
```

## Data Flow
```
User input → argparse → args.logfile → parse_log() → data dict
                                                         ↓
                                          summary / export / graphs / anomalies / reporter
```

## Interview Points
- The `logfile` argument uses `nargs="?"` to make it optional — this is what enables interactive mode to prompt for a file at runtime
- The flag-based and interactive paths share the SAME analysis functions — no code duplication
- Config is loaded ONCE before branching, so both modes use the same configuration

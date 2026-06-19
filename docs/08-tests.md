# tests/ — Test Suite

## What It Does
Contains 79 pytest tests that verify every module works correctly.

## File Location
`tests/` directory

## Test Files

### conftest.py — Shared Fixtures
Defines reusable test data (no real log files needed):

| Fixture | Description |
|---------|------------|
| `empty_data` | Standard data dict with all keys but empty lists |
| `sample_data` | Realistic 30-second flight near New Delhi (28.6139, 77.2090) |
| `low_battery_data` | Battery entries crossing the 20% threshold |
| `altitude_drop_data` | Position entries with a 15m sudden drop |
| `excessive_attitude_data` | Extreme roll (7.0 rad ≈ 401°) |
| `bin_style_data` | Data mimicking .bin quirks (None battery, boot timestamps) |
| `sample_config` | Config with tighter thresholds for testing |

### test_analyzer.py — CLI Tests
- `test_no_args_exits` — running with no args exits with code 1
- `test_summary_flag` — `--summary` calls correct functions
- `test_all_flag` — `--all` triggers all four analysis steps
- `test_no_messages_exits` — empty log exits with code 0
- `test_file_not_found_exits` — missing file exits with code 1

### test_anomalies.py — Anomaly Detection Tests
Tests all three check functions with specific data that should/shouldn't trigger warnings.

### test_config.py — Configuration Tests
- Default config returns all expected keys
- YAML override merges correctly with defaults
- Missing config file silently returns defaults

### test_exporter.py — CSV Export Tests
- Each exporter produces correct CSV file
- Handles empty data gracefully
- Correct column selection

### test_graphs.py — Graph Generation Tests
- Each graph function produces a PNG file
- Handles empty data without crashing
- File cleanup after tests

### test_parser_helpers.py — Parser Utility Tests
- `_safe_datetime` handles boot-relative timestamps
- `validate_log_file` checks extensions correctly
- `_timestamp_from_msg` extracts timestamps

### test_parser_io.py — Parser Integration Tests
- Tests actual .tlog and .bin parsing with real sample files

### test_summary.py — Summary Computation Tests
- Haversine distance calculation
- Duration formatting
- Speed computation
- Summary generation with sample data

## Running Tests
```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=.

# Run specific test file
pytest tests/test_anomalies.py -v
```

## Interview Points
- All tests use synthetic data — no real log files in the test suite (fast, deterministic)
- Fixtures in conftest.py follow the Arrange-Act-Assert pattern
- Mock objects (`@patch`) used to isolate units — parser is mocked in analyzer tests
- Tests verify both success paths AND error paths (file not found, empty log, etc.)

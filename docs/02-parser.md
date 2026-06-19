# parser.py — Log File Parser

## What It Does
Reads raw drone log files (.tlog or .bin) and converts them into a **standardized Python dictionary** that all other modules can use without knowing the original format.

## File Location
`parser.py` (project root)

## The Problem It Solves
MAVLink `.tlog` and ArduPilot `.bin` files use DIFFERENT message names, field names, and unit encodings:
- `.tlog`: `GPS_RAW_INT` with `lat` in degE7 (latitude * 10^7)
- `.bin`: `GPS` with `Lat` in plain degrees

This parser normalizes both into ONE common schema.

## The Common Data Schema
```python
{
    "gps": [...],           # GPS coordinates + speed
    "position": [...],      # Altitude + velocity + heading
    "battery": [...],       # Voltage, current, remaining %
    "attitude": [...],      # Roll, pitch, yaw (in radians)
    "events": [...],        # Arm/disarm/mode change events
    "meta": {               # File metadata
        "filepath": "...",
        "total_messages": 100,
        "parsed_messages": 42,
        "start_time": 1700000000.0,
        "end_time": 1700000027.0,
    }
}
```

## Key Functions

### validate_log_file(filepath)
- Checks file exists (`os.path.isfile`)
- Checks extension is `.tlog` or `.bin`
- Returns absolute path

### parse_tlog(filepath) — for .tlog files
1. Opens file with `mavutil.mavlink_connection()`
2. Loops through messages with `recv_match(blocking=False)`
3. Filters to SUPPORTED_MESSAGES: `GPS_RAW_INT`, `GLOBAL_POSITION_INT`, `SYS_STATUS`, `ATTITUDE`, `STATUSTEXT`
4. Dispatches each message to its parser function via `_PARSERS` dict
5. Converts raw units: degE7→degrees, mm→meters, cm/s→m/s, mV→volts

### parse_bin(filepath) — for .bin files
Same flow but with DataFlash messages: `GPS`, `ATT`, `BAT`, `MSG`, `MODE`, `EV`

### _post_process_bin_data(data, config)
DataFlash logs are MISSING some fields. This function:
1. **Reconstructs `relative_alt`** — uses first GPS altitude as "home" reference, computes offset for each point
2. **Estimates `battery_remaining`** — auto-detects LiPo cell count from max voltage, applies linear voltage-to-percentage mapping

### parse_log(filepath, config) — THE MAIN API
Auto-detects format from extension, routes to `parse_tlog()` or `parse_bin()`.

## Unit Conversions in .tlog Parsing
| Raw Value | Conversion | Example |
|-----------|-----------|---------|
| `msg.lat` (degE7) | `/ 1e7` | 286139000 → 28.6139° |
| `msg.alt` (mm) | `/ 1000.0` | 50000 → 50.0 m |
| `msg.vel` (cm/s) | `/ 100.0` | 1500 → 15.0 m/s |
| `msg.voltage_battery` (mV) | `/ 1000.0` | 12600 → 12.6 V |
| `msg.roll` (radians) | kept as-is | 0.1 rad |

## Why .bin Posts Processing Is Needed
DataFlash logs don't have `GLOBAL_POSITION_INT` equivalent. The parser:
- Creates position entries from GPS data (adds `relative_alt` = GPS alt - home alt)
- Estimates battery % from voltage (since `battery_remaining` field doesn't exist in BAT messages)
- Sets `vx`, `vy`, `vz`, `heading` to `None` (unavailable)

## Interview Points
- "Schema normalization" pattern — different inputs, same output structure
- Dispatch table pattern (`_PARSERS` dict) instead of if/elif chains
- Defensive coding: `None` handling for missing fields ensures downstream modules never crash
- Boot-relative timestamps (DataFlash) detected by checking `< year 2000 epoch`

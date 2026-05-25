import os
import sys
import math
from datetime import datetime
from pymavlink import mavutil

# ---------------------------------------------------------------------------
# Supported MAVLink message types for .tlog telemetry logs
# ---------------------------------------------------------------------------
SUPPORTED_MESSAGES = {
    "GPS_RAW_INT",
    "GLOBAL_POSITION_INT",
    "SYS_STATUS",
    "ATTITUDE",
}

# ---------------------------------------------------------------------------
# Supported DataFlash message types for .bin logs
# ---------------------------------------------------------------------------
SUPPORTED_BIN_MESSAGES = {
    "GPS",
    "ATT",
    "BAT",
}

# ---------------------------------------------------------------------------
# Supported file extensions
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS = {".tlog", ".bin"}

# Epoch timestamp for year 2000 — used to detect boot-relative timestamps
# that are common in DataFlash .bin logs.
_EPOCH_YEAR_2000 = 946684800


# ===================================================================
#  Validation helpers
# ===================================================================

def validate_tlog_file(filepath: str) -> str:
    """Validate that *filepath* exists and has a .tlog extension.

    Kept for backward compatibility — existing callers can still use this.
    """
    abs_path = os.path.abspath(filepath)

    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"Log file not found: {abs_path}")

    if not abs_path.lower().endswith(".tlog"):
        raise ValueError(
            f"Invalid file type. Expected a .tlog file, got: {os.path.basename(abs_path)}"
        )

    return abs_path


def validate_log_file(filepath: str) -> str:
    """Validate that *filepath* exists and has a supported extension (.tlog or .bin).

    Returns the absolute path on success.
    Raises FileNotFoundError or ValueError on failure.
    """
    abs_path = os.path.abspath(filepath)

    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"Log file not found: {abs_path}")

    ext = os.path.splitext(abs_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Expected one of: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    return abs_path


# ===================================================================
#  Timestamp / datetime helpers
# ===================================================================

def _timestamp_from_msg(msg) -> float:
    """Extract the timestamp attribute that pymavlink attaches to every message."""
    return getattr(msg, "_timestamp", 0.0)


def _safe_datetime(timestamp: float):
    """Convert a Unix-epoch timestamp to a human-readable datetime string.

    DataFlash .bin logs sometimes use boot-relative timestamps (seconds
    since power-on) rather than true Unix epochs.  If the timestamp is
    earlier than the year 2000 we treat it as boot-relative and return
    None instead of a misleading date.
    """
    if timestamp < _EPOCH_YEAR_2000:
        return None
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


# ===================================================================
#  .tlog (MAVLink telemetry) message parsers
# ===================================================================
# These functions extract fields from standard MAVLink messages and
# convert raw integer encodings into human-readable units.
# ===================================================================

def _parse_gps_raw_int(msg, timestamp: float) -> dict:
    """Parse a MAVLink GPS_RAW_INT message."""
    return {
        "timestamp": timestamp,
        "datetime": _safe_datetime(timestamp),
        "lat": msg.lat / 1e7,           # degE7 → degrees
        "lon": msg.lon / 1e7,           # degE7 → degrees
        "alt": msg.alt / 1000.0,        # mm    → metres
        "speed": msg.vel / 100.0,       # cm/s  → m/s
        "satellites": msg.satellites_visible,
        "fix_type": msg.fix_type,       # 0-1 no fix, 2=2D, 3=3D …
    }


def _parse_global_position_int(msg, timestamp: float) -> dict:
    """Parse a MAVLink GLOBAL_POSITION_INT message."""
    return {
        "timestamp": timestamp,
        "datetime": _safe_datetime(timestamp),
        "lat": msg.lat / 1e7,
        "lon": msg.lon / 1e7,
        "alt": msg.alt / 1000.0,                  # mm → m
        "relative_alt": msg.relative_alt / 1000.0, # mm → m
        "vx": msg.vx / 100.0,                      # cm/s → m/s
        "vy": msg.vy / 100.0,                      # cm/s → m/s
        "vz": msg.vz / 100.0,                      # cm/s → m/s
        "heading": msg.hdg / 100.0,                 # cdeg → deg
    }


def _parse_sys_status(msg, timestamp: float) -> dict:
    """Parse a MAVLink SYS_STATUS message."""
    return {
        "timestamp": timestamp,
        "datetime": _safe_datetime(timestamp),
        "voltage": msg.voltage_battery / 1000.0,  # mV → V
        "current": msg.current_battery / 100.0,   # cA → A
        "battery_remaining": msg.battery_remaining, # %
    }


def _parse_attitude(msg, timestamp: float) -> dict:
    """Parse a MAVLink ATTITUDE message (values in radians)."""
    return {
        "timestamp": timestamp,
        "datetime": _safe_datetime(timestamp),
        "roll": msg.roll,               # radians
        "pitch": msg.pitch,             # radians
        "yaw": msg.yaw,                 # radians
        "rollspeed": msg.rollspeed,     # rad/s
        "pitchspeed": msg.pitchspeed,   # rad/s
        "yawspeed": msg.yawspeed,       # rad/s
    }


# Dispatch tables — map message type name → parser function
_PARSERS = {
    "GPS_RAW_INT": _parse_gps_raw_int,
    "GLOBAL_POSITION_INT": _parse_global_position_int,
    "SYS_STATUS": _parse_sys_status,
    "ATTITUDE": _parse_attitude,
}

# Map message type name → storage key in the output data dict
_STORAGE_KEYS = {
    "GPS_RAW_INT": "gps",
    "GLOBAL_POSITION_INT": "position",
    "SYS_STATUS": "battery",
    "ATTITUDE": "attitude",
}


# ===================================================================
#  .bin (ArduPilot DataFlash) message parsers
# ===================================================================
# DataFlash logs use DIFFERENT message names and field names than
# MAVLink telemetry.  Values are already in human-readable units
# (degrees, metres, volts) so no scaling conversions are needed.
#
# We map each DataFlash message into the SAME dict structure used
# for .tlog so that downstream modules never need to know which
# format the log came from.
# ===================================================================

def _parse_bin_gps(msg, timestamp: float) -> dict:
    """Parse a DataFlash GPS message → same schema as GPS_RAW_INT.

    DataFlash GPS fields are already in human-readable units:
      Lat/Lng in degrees, Alt in metres, Spd in m/s.
    """
    return {
        "timestamp": timestamp,
        "datetime": _safe_datetime(timestamp),
        "lat": msg.Lat,               # degrees (no conversion needed)
        "lon": msg.Lng,               # degrees
        "alt": msg.Alt,               # metres
        "speed": msg.Spd,             # m/s
        "satellites": msg.NSats,
        "fix_type": msg.Status,       # 0=no fix, 2=2D, 3=3D …
    }


def _parse_bin_att(msg, timestamp: float) -> dict:
    """Parse a DataFlash ATT message → same schema as ATTITUDE.

    IMPORTANT: DataFlash ATT values are in DEGREES, whereas MAVLink
    ATTITUDE values are in RADIANS.  We convert degrees → radians here
    so that downstream modules receive a consistent unit.

    DataFlash ATT does NOT include angular rates (rollspeed, pitchspeed,
    yawspeed) — these are set to None.
    """
    return {
        "timestamp": timestamp,
        "datetime": _safe_datetime(timestamp),
        "roll": math.radians(msg.Roll),    # deg → rad for consistency
        "pitch": math.radians(msg.Pitch),  # deg → rad
        "yaw": math.radians(msg.Yaw),      # deg → rad
        "rollspeed": None,                  # not available in DataFlash ATT
        "pitchspeed": None,
        "yawspeed": None,
    }


def _parse_bin_bat(msg, timestamp: float) -> dict:
    """Parse a DataFlash BAT message → same schema as SYS_STATUS.

    DataFlash BAT does NOT include battery_remaining percentage —
    this is set to None.  Downstream modules must handle None safely.
    """
    return {
        "timestamp": timestamp,
        "datetime": _safe_datetime(timestamp),
        "voltage": msg.Volt,          # volts (no conversion needed)
        "current": msg.Curr,          # amps
        "battery_remaining": None,    # not available in DataFlash BAT
    }


# Dispatch tables for DataFlash .bin messages
_BIN_PARSERS = {
    "GPS": _parse_bin_gps,
    "ATT": _parse_bin_att,
    "BAT": _parse_bin_bat,
}

_BIN_STORAGE_KEYS = {
    "GPS": "gps",
    "ATT": "attitude",
    "BAT": "battery",
}


# ===================================================================
#  Helper: create an empty data dict (common structure)
# ===================================================================

def _make_empty_data(abs_path: str) -> dict:
    """Return a fresh data dict with the standard top-level keys.

    Every parser function (parse_tlog, parse_bin) returns this
    same structure so downstream modules never care about the
    source format.
    """
    return {
        "gps": [],
        "position": [],
        "battery": [],
        "attitude": [],
        "meta": {
            "filepath": abs_path,
            "total_messages": 0,
            "parsed_messages": 0,
            "start_time": None,
            "end_time": None,
        },
    }


# ===================================================================
#  parse_tlog  —  parse MAVLink .tlog telemetry logs
# ===================================================================

def parse_tlog(filepath: str) -> dict:
    """Parse a MAVLink .tlog telemetry log file.

    Returns the standard data dict consumed by all downstream modules.
    This function is preserved for backward compatibility; new code
    should prefer ``parse_log()`` which auto-detects the format.
    """
    abs_path = validate_tlog_file(filepath)
    try:
        mav = mavutil.mavlink_connection(abs_path)
    except Exception as exc:
        print(f"[ERROR] Failed to open MAVLink log: {exc}")
        sys.exit(1)

    data = _make_empty_data(abs_path)

    print(f"[INFO] Parsing log file: {os.path.basename(abs_path)}")
    print(f"[INFO] Detected log type: .tlog (MAVLink telemetry)")

    while True:
        try:
            msg = mav.recv_match(blocking=False)
        except Exception:
            # Skip corrupted or malformed packets
            continue
        finally:
            pass
        if msg is None:
            break  # End of file

        data["meta"]["total_messages"] += 1
        msg_type = msg.get_type()

        # Only process messages we care about
        if msg_type not in SUPPORTED_MESSAGES:
            continue

        timestamp = _timestamp_from_msg(msg)

        # Track time range
        if data["meta"]["start_time"] is None:
            data["meta"]["start_time"] = timestamp
        data["meta"]["end_time"] = timestamp

        # Dispatch to the appropriate parser and store the result
        parser_fn = _PARSERS[msg_type]
        parsed = parser_fn(msg, timestamp)

        storage_key = _STORAGE_KEYS[msg_type]
        data[storage_key].append(parsed)
        data["meta"]["parsed_messages"] += 1

    print(
        f"[INFO] Parsed {data['meta']['parsed_messages']} relevant messages "
        f"out of {data['meta']['total_messages']} total."
    )
    _print_record_counts(data)

    return data


# ===================================================================
#  parse_bin  —  parse ArduPilot DataFlash .bin logs
# ===================================================================

def parse_bin(filepath: str) -> dict:
    """Parse an ArduPilot DataFlash .bin binary log file.

    Returns the SAME data dict structure as ``parse_tlog()`` so that
    all downstream modules work identically regardless of log format.

    DataFlash .bin logs do NOT contain GLOBAL_POSITION_INT equivalent
    data, so the ``"position"`` list will be empty.  We do NOT fabricate
    unavailable telemetry.
    """
    abs_path = validate_log_file(filepath)
    try:
        mav = mavutil.mavlink_connection(abs_path)
    except Exception as exc:
        print(f"[ERROR] Failed to open DataFlash log: {exc}")
        sys.exit(1)

    data = _make_empty_data(abs_path)

    print(f"[INFO] Parsing log file: {os.path.basename(abs_path)}")
    print(f"[INFO] Detected log type: .bin (ArduPilot DataFlash)")

    while True:
        try:
            msg = mav.recv_match(blocking=False)
        except Exception:
            # Skip corrupted or malformed packets
            continue
        if msg is None:
            break  # End of file

        data["meta"]["total_messages"] += 1
        msg_type = msg.get_type()

        # Only process DataFlash messages we care about
        if msg_type not in SUPPORTED_BIN_MESSAGES:
            continue

        timestamp = _timestamp_from_msg(msg)

        # Track time range
        if data["meta"]["start_time"] is None:
            data["meta"]["start_time"] = timestamp
        data["meta"]["end_time"] = timestamp

        # Dispatch to the appropriate DataFlash parser
        try:
            parser_fn = _BIN_PARSERS[msg_type]
            parsed = parser_fn(msg, timestamp)
        except (AttributeError, TypeError) as exc:
            # Some DataFlash messages may have unexpected field layouts
            # depending on firmware version — skip gracefully.
            print(f"[WARN] Skipping malformed {msg_type} message: {exc}")
            continue

        storage_key = _BIN_STORAGE_KEYS[msg_type]
        data[storage_key].append(parsed)
        data["meta"]["parsed_messages"] += 1

    print(
        f"[INFO] Parsed {data['meta']['parsed_messages']} relevant messages "
        f"out of {data['meta']['total_messages']} total."
    )
    _print_record_counts(data)

    return data


# ===================================================================
#  parse_log  —  unified entry point (auto-detects format)
# ===================================================================

def parse_log(filepath: str) -> dict:
    """Parse a log file, auto-detecting the format from its extension.

    This is the MAIN public API.  It routes to ``parse_tlog()`` or
    ``parse_bin()`` based on the file extension.

    Returns the standard data dict consumed by all downstream modules.
    """
    abs_path = validate_log_file(filepath)
    ext = os.path.splitext(abs_path)[1].lower()

    if ext == ".tlog":
        return parse_tlog(filepath)
    elif ext == ".bin":
        return parse_bin(filepath)
    else:
        # Should never reach here because validate_log_file checks,
        # but guard anyway.
        raise ValueError(f"Unsupported log format: {ext}")


# ===================================================================
#  Debug / verification helpers
# ===================================================================

def _print_record_counts(data: dict) -> None:
    """Print per-category record counts for quick verification."""
    print(f"[INFO]   GPS records     : {len(data['gps'])}")
    print(f"[INFO]   Position records: {len(data['position'])}")
    print(f"[INFO]   Battery records : {len(data['battery'])}")
    print(f"[INFO]   Attitude records: {len(data['attitude'])}")

import os
import sys
import math
from datetime import datetime
from pymavlink import mavutil
SUPPORTED_MESSAGES = {
    "GPS_RAW_INT",
    "GLOBAL_POSITION_INT",
    "SYS_STATUS",
    "ATTITUDE",
    "STATUSTEXT",
}
SUPPORTED_BIN_MESSAGES = {
    "GPS",
    "ATT",
    "BAT",
    "MSG",
    "MODE",
    "EV",
}
SUPPORTED_EXTENSIONS = {".tlog", ".bin"}
_EPOCH_YEAR_2000 = 946684800
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
def _parse_gps_raw_int(msg, timestamp: float) -> dict:
    """Parse a MAVLink GPS_RAW_INT message."""
    return {
        "timestamp": timestamp,
        "datetime": _safe_datetime(timestamp),
        "lat": msg.lat / 1e7,                            
        "lon": msg.lon / 1e7,                            
        "alt": msg.alt / 1000.0,                        
        "speed": msg.vel / 100.0,                    
        "satellites": msg.satellites_visible,
        "fix_type": msg.fix_type,                                 
    }
def _parse_global_position_int(msg, timestamp: float) -> dict:
    """Parse a MAVLink GLOBAL_POSITION_INT message."""
    return {
        "timestamp": timestamp,
        "datetime": _safe_datetime(timestamp),
        "lat": msg.lat / 1e7,
        "lon": msg.lon / 1e7,
        "alt": msg.alt / 1000.0,                          
        "relative_alt": msg.relative_alt / 1000.0,         
        "vx": msg.vx / 100.0,                                  
        "vy": msg.vy / 100.0,                                  
        "vz": msg.vz / 100.0,                                  
        "heading": msg.hdg / 100.0,                             
    }
def _parse_sys_status(msg, timestamp: float) -> dict:
    """Parse a MAVLink SYS_STATUS message."""
    return {
        "timestamp": timestamp,
        "datetime": _safe_datetime(timestamp),
        "voltage": msg.voltage_battery / 1000.0,          
        "current": msg.current_battery / 100.0,           
        "battery_remaining": msg.battery_remaining,    
    }
def _parse_attitude(msg, timestamp: float) -> dict:
    """Parse a MAVLink ATTITUDE message (values in radians)."""
    return {
        "timestamp": timestamp,
        "datetime": _safe_datetime(timestamp),
        "roll": msg.roll,                        
        "pitch": msg.pitch,                      
        "yaw": msg.yaw,                          
        "rollspeed": msg.rollspeed,            
        "pitchspeed": msg.pitchspeed,          
        "yawspeed": msg.yawspeed,              
    }
def _parse_statustext(msg, timestamp: float) -> dict | None:
    """Parse a MAVLink STATUSTEXT message for major events."""
    text = getattr(msg, "text", "")
    lower_text = text.lower()
    if any(k in lower_text for k in ["arm", "disarm", "takeoff", "land", "mode"]):
        return {
            "timestamp": timestamp,
            "datetime": _safe_datetime(timestamp),
            "name": text,
        }
    return None
_PARSERS = {
    "GPS_RAW_INT": _parse_gps_raw_int,
    "GLOBAL_POSITION_INT": _parse_global_position_int,
    "SYS_STATUS": _parse_sys_status,
    "ATTITUDE": _parse_attitude,
    "STATUSTEXT": _parse_statustext,
}
_STORAGE_KEYS = {
    "GPS_RAW_INT": "gps",
    "GLOBAL_POSITION_INT": "position",
    "SYS_STATUS": "battery",
    "ATTITUDE": "attitude",
    "STATUSTEXT": "events",
}
def _parse_bin_gps(msg, timestamp: float) -> dict:
    """Parse a DataFlash GPS message → same schema as GPS_RAW_INT.
    DataFlash GPS fields are already in human-readable units:
      Lat/Lng in degrees, Alt in metres, Spd in m/s.
    """
    return {
        "timestamp": timestamp,
        "datetime": _safe_datetime(timestamp),
        "lat": msg.Lat,                                               
        "lon": msg.Lng,                        
        "alt": msg.Alt,                       
        "speed": msg.Spd,                  
        "satellites": msg.NSats,
        "fix_type": msg.Status,                               
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
        "roll": math.radians(msg.Roll),                               
        "pitch": math.radians(msg.Pitch),             
        "yaw": math.radians(msg.Yaw),                 
        "rollspeed": None,                                                  
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
        "voltage": msg.Volt,                                        
        "current": msg.Curr,                
        "battery_remaining": None,                                    
    }
def _parse_bin_msg(msg, timestamp: float) -> dict | None:
    text = getattr(msg, "Message", "")
    lower_text = text.lower()
    if any(k in lower_text for k in ["arm", "disarm", "takeoff", "land", "mode"]):
        return {
            "timestamp": timestamp,
            "datetime": _safe_datetime(timestamp),
            "name": text,
        }
    return None
def _parse_bin_mode(msg, timestamp: float) -> dict | None:
    mode_num = getattr(msg, "ModeNum", getattr(msg, "Mode", "Unknown"))
    return {
        "timestamp": timestamp,
        "datetime": _safe_datetime(timestamp),
        "name": f"Mode {mode_num}",
    }
def _parse_bin_ev(msg, timestamp: float) -> dict | None:
    ev_id = getattr(msg, "Id", None)
    if ev_id == 10:
        name = "Armed"
    elif ev_id == 11:
        name = "Disarmed"
    elif ev_id == 15:
        name = "Auto Armed"
    else:
        return None
    return {
        "timestamp": timestamp,
        "datetime": _safe_datetime(timestamp),
        "name": name,
    }
_BIN_PARSERS = {
    "GPS": _parse_bin_gps,
    "ATT": _parse_bin_att,
    "BAT": _parse_bin_bat,
    "MSG": _parse_bin_msg,
    "MODE": _parse_bin_mode,
    "EV": _parse_bin_ev,
}
_BIN_STORAGE_KEYS = {
    "GPS": "gps",
    "ATT": "attitude",
    "BAT": "battery",
    "MSG": "events",
    "MODE": "events",
    "EV": "events",
}
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
        "events": [],
        "meta": {
            "filepath": abs_path,
            "total_messages": 0,
            "parsed_messages": 0,
            "start_time": None,
            "end_time": None,
        },
    }
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
            continue
        finally:
            pass
        if msg is None:
            break               
        data["meta"]["total_messages"] += 1
        msg_type = msg.get_type()
        if msg_type not in SUPPORTED_MESSAGES:
            continue
        timestamp = _timestamp_from_msg(msg)
        if data["meta"]["start_time"] is None:
            data["meta"]["start_time"] = timestamp
        data["meta"]["end_time"] = timestamp
        parser_fn = _PARSERS[msg_type]
        parsed = parser_fn(msg, timestamp)
        if parsed is not None:
            storage_key = _STORAGE_KEYS[msg_type]
            data[storage_key].append(parsed)
            data["meta"]["parsed_messages"] += 1
    print(
        f"[INFO] Parsed {data['meta']['parsed_messages']} relevant messages "
        f"out of {data['meta']['total_messages']} total."
    )
    _print_record_counts(data)
    return data
def parse_bin(filepath: str, config: dict | None = None) -> dict:
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
            continue
        if msg is None:
            break               
        data["meta"]["total_messages"] += 1
        msg_type = msg.get_type()
        if msg_type not in SUPPORTED_BIN_MESSAGES:
            continue
        timestamp = _timestamp_from_msg(msg)
        if data["meta"]["start_time"] is None:
            data["meta"]["start_time"] = timestamp
        data["meta"]["end_time"] = timestamp
        try:
            parser_fn = _BIN_PARSERS[msg_type]
            parsed = parser_fn(msg, timestamp)
        except (AttributeError, TypeError) as exc:
            print(f"[WARN] Skipping malformed {msg_type} message: {exc}")
            continue
        if parsed is not None:
            storage_key = _BIN_STORAGE_KEYS[msg_type]
            data[storage_key].append(parsed)
            data["meta"]["parsed_messages"] += 1
    _post_process_bin_data(data, config=config)
    print(
        f"[INFO] Parsed {data['meta']['parsed_messages']} relevant messages "
        f"out of {data['meta']['total_messages']} total."
    )
    _print_record_counts(data)
    return data
def _post_process_bin_data(data: dict, config: dict | None = None) -> None:
    """Post-process .bin data to recover missing fields through estimation.
    1. Reconstructs 'relative_alt' in the position array by using the first 
       GPS altitude as a home reference point.
    2. Estimates 'battery_remaining' percentage by auto-detecting LiPo cell 
       count from max voltage, and applying a basic linear discharge curve.
    If *config* is provided, cell voltage values are read from
    ``config["battery_estimation"]`` instead of the hardcoded defaults.
    """
    if config is not None:
        batt_cfg = config.get("battery_estimation", {})
        cell_full = batt_cfg.get("cell_voltage_full", 4.2)
        cell_empty = batt_cfg.get("cell_voltage_empty", 3.5)
    else:
        cell_full = 4.2
        cell_empty = 3.5
    if data["gps"] and not data["position"]:
        home_alt = data["gps"][0]["alt"]
        for g in data["gps"]:
            data["position"].append({
                "timestamp": g["timestamp"],
                "datetime": g["datetime"],
                "lat": g["lat"],
                "lon": g["lon"],
                "alt": g["alt"],
                "relative_alt": g["alt"] - home_alt,
                "vx": None,
                "vy": None,
                "vz": None,
                "heading": None
            })
    if data["battery"]:
        max_v = max(b["voltage"] for b in data["battery"])
        if max_v > 0:
            cells = max(1, round(max_v / cell_full))
            full_v = cell_full * cells
            empty_v = cell_empty * cells
            for b in data["battery"]:
                if b.get("battery_remaining") is None:
                    pct = (b["voltage"] - empty_v) / (full_v - empty_v) * 100
                    pct = max(0, min(100, pct))
                    b["battery_remaining"] = round(pct)
def parse_log(filepath: str, config: dict | None = None) -> dict:
    """Parse a log file, auto-detecting the format from its extension.
    This is the MAIN public API.  It routes to ``parse_tlog()`` or
    ``parse_bin()`` based on the file extension.
    Parameters
    ----------
    config : dict or None
        Optional configuration dict.  Forwarded to ``parse_bin()`` for
        battery estimation parameters.
    Returns the standard data dict consumed by all downstream modules.
    """
    abs_path = validate_log_file(filepath)
    ext = os.path.splitext(abs_path)[1].lower()
    if ext == ".tlog":
        return parse_tlog(filepath)
    elif ext == ".bin":
        return parse_bin(filepath, config=config)
    else:
        raise ValueError(f"Unsupported log format: {ext}")
def _print_record_counts(data: dict) -> None:
    """Print per-category record counts for quick verification."""
    print(f"[INFO]   GPS records     : {len(data['gps'])}")
    print(f"[INFO]   Position records: {len(data['position'])}")
    print(f"[INFO]   Battery records : {len(data['battery'])}")
    print(f"[INFO]   Attitude records: {len(data['attitude'])}")
    print(f"[INFO]   Event records   : {len(data['events'])}")

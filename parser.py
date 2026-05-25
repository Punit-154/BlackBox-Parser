import os
import sys
from datetime import datetime
from pymavlink import mavutil

SUPPORTED_MESSAGES = {
    "GPS_RAW_INT",
    "GLOBAL_POSITION_INT",
    "SYS_STATUS",
    "ATTITUDE",
}

def validate_tlog_file(filepath: str) -> str:
    
    abs_path = os.path.abspath(filepath)

    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"Log file not found: {abs_path}")

    if not abs_path.lower().endswith(".tlog"):
        raise ValueError(
            f"Invalid file type. Expected a .tlog file, got: {os.path.basename(abs_path)}"
        )

    return abs_path


def _timestamp_from_msg(msg) -> float:
    return getattr(msg, "_timestamp", 0.0)


def _parse_gps_raw_int(msg, timestamp: float) -> dict:
    
    return {
        "timestamp": timestamp,
        "datetime": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
        "lat": msg.lat / 1e7,           
        "lon": msg.lon / 1e7,           
        "alt": msg.alt / 1000.0,        
        "speed": msg.vel / 100.0,       
        "satellites": msg.satellites_visible,
        "fix_type": msg.fix_type,       
    }


def _parse_global_position_int(msg, timestamp: float) -> dict:
    
    return {
        "timestamp": timestamp,
        "datetime": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
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
    
    return {
        "timestamp": timestamp,
        "datetime": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
        "voltage": msg.voltage_battery / 1000.0,  
        "current": msg.current_battery / 100.0,   
        "battery_remaining": msg.battery_remaining,  
    }


def _parse_attitude(msg, timestamp: float) -> dict:
    
    return {
        "timestamp": timestamp,
        "datetime": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
        "roll": msg.roll,               
        "pitch": msg.pitch,             
        "yaw": msg.yaw,                 
        "rollspeed": msg.rollspeed,     
        "pitchspeed": msg.pitchspeed,   
        "yawspeed": msg.yawspeed,       
    }

_PARSERS = {
    "GPS_RAW_INT": _parse_gps_raw_int,
    "GLOBAL_POSITION_INT": _parse_global_position_int,
    "SYS_STATUS": _parse_sys_status,
    "ATTITUDE": _parse_attitude,
}


def parse_tlog(filepath: str) -> dict:
    
    abs_path = validate_tlog_file(filepath)
    try:
        mav = mavutil.mavlink_connection(abs_path)
    except Exception as exc:
        print(f"[ERROR] Failed to open MAVLink log: {exc}")
        sys.exit(1)

    
    data = {
        "gps_raw": [],
        "global_position": [],
        "sys_status": [],
        "attitude": [],
        "meta": {
            "filepath": abs_path,
            "total_messages": 0,
            "parsed_messages": 0,
            "start_time": None,
            "end_time": None,
        },
    }

    
    _STORAGE_KEYS = {
        "GPS_RAW_INT": "gps_raw",
        "GLOBAL_POSITION_INT": "global_position",
        "SYS_STATUS": "sys_status",
        "ATTITUDE": "attitude",
    }

    print(f"[INFO] Parsing log file: {os.path.basename(abs_path)}")

    
    
    
    
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

        storage_key = _STORAGE_KEYS[msg_type]
        data[storage_key].append(parsed)
        data["meta"]["parsed_messages"] += 1

    print(
        f"[INFO] Parsed {data['meta']['parsed_messages']} relevant messages "
        f"out of {data['meta']['total_messages']} total."
    )

    return data

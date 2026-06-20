import math
from datetime import datetime
BATTERY_LOW_THRESHOLD = 20          
ALTITUDE_DROP_THRESHOLD = 10.0      
ROLL_LIMIT_DEG = 360.0               
PITCH_LIMIT_DEG = 360.0              
_EPOCH_YEAR_2000 = 946684800
def _ts_to_time_str(timestamp: float) -> str:
    """Convert a timestamp to HH:MM:SS string.
    Safely handles boot-relative timestamps (common in DataFlash .bin
    logs) by returning a relative-time label instead of crashing.
    """
    if timestamp < _EPOCH_YEAR_2000:
        return f"T+{timestamp:.0f}s"
    return datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
def check_low_battery(data: dict, threshold: int = BATTERY_LOW_THRESHOLD) -> list[str]:
    """Check for low battery events.
    Safely skips entries where battery_remaining is None (common with
    DataFlash .bin logs where BAT messages lack this field).
    """
    warnings_list = []
    already_warned = False
    for entry in data["battery"]:
        remaining = entry.get("battery_remaining")
        if remaining is None or remaining < 0:
            continue
        if remaining < threshold and not already_warned:
            time_str = _ts_to_time_str(entry["timestamp"])
            warnings_list.append(
                f"! LOW BATTERY: Battery dropped below {threshold}% "
                f"(was {remaining}%) at {time_str}"
            )
            already_warned = True
    return warnings_list
def check_altitude_drop(data: dict, threshold: float = ALTITUDE_DROP_THRESHOLD) -> list[str]:
    """Check for sudden altitude drops.
    Safely handles None values in relative_alt (filters them out
    before computing differences).
    """
    warnings_list = []
    records = [
        r for r in data["position"]
        if r.get("relative_alt") is not None
    ]
    for i in range(1, len(records)):
        prev_alt = records[i - 1]["relative_alt"]
        curr_alt = records[i]["relative_alt"]
        drop = prev_alt - curr_alt
        if drop >= threshold:
            time_str = _ts_to_time_str(records[i]["timestamp"])
            warnings_list.append(
                f"! ALTITUDE DROP: Sudden drop of {drop:.1f} m detected at {time_str} "
                f"({prev_alt:.1f} m -> {curr_alt:.1f} m)"
            )
    return warnings_list
def check_excessive_attitude(
    data: dict,
    roll_limit: float = ROLL_LIMIT_DEG,
    pitch_limit: float = PITCH_LIMIT_DEG,
) -> list[str]:
    """Check for excessive roll or pitch angles.
    Safely skips entries where roll or pitch is None.
    """
    warnings_list = []
    for entry in data["attitude"]:
        roll = entry.get("roll")
        pitch = entry.get("pitch")
        if roll is None or pitch is None:
            continue
        roll_deg = abs(math.degrees(roll))
        pitch_deg = abs(math.degrees(pitch))
        time_str = _ts_to_time_str(entry["timestamp"])
        if roll_deg > roll_limit:
            warnings_list.append(
                f"! EXCESSIVE ROLL: Roll angle of {roll_deg:.1f} degrees "
                f"exceeds limit of {roll_limit:.0f} degrees at {time_str}"
            )
        if pitch_deg > pitch_limit:
            warnings_list.append(
                f"! EXCESSIVE PITCH: Pitch angle of {pitch_deg:.1f} degrees "
                f"exceeds limit of {pitch_limit:.0f} degrees at {time_str}"
            )
    return warnings_list
def run_all_checks(data: dict, config: dict | None = None) -> list[str]:
    """Run every anomaly check and return a combined list of warnings.
    If *config* is provided, threshold values are read from
    ``config["thresholds"]`` and forwarded to the individual check
    functions.  Otherwise the module-level defaults are used.
    """
    kwargs_battery: dict = {}
    kwargs_altitude: dict = {}
    kwargs_attitude: dict = {}
    if config is not None:
        th = config.get("thresholds", {})
        if "battery_low_percent" in th:
            kwargs_battery["threshold"] = th["battery_low_percent"]
        if "altitude_drop_m" in th:
            kwargs_altitude["threshold"] = th["altitude_drop_m"]
        if "roll_limit_deg" in th:
            kwargs_attitude["roll_limit"] = th["roll_limit_deg"]
        if "pitch_limit_deg" in th:
            kwargs_attitude["pitch_limit"] = th["pitch_limit_deg"]
    all_warnings = []
    all_warnings.extend(check_low_battery(data, **kwargs_battery))
    all_warnings.extend(check_altitude_drop(data, **kwargs_altitude))
    all_warnings.extend(check_excessive_attitude(data, **kwargs_attitude))
    return all_warnings
def print_warnings(warning_list: list[str]) -> None:
    print()
    print("=" * 45)
    print("            FLIGHT WARNINGS")
    print("=" * 45)
    print()
    if not warning_list:
        print("  [OK] No warnings detected. Flight looks clean!")
    else:
        print(f"  Found {len(warning_list)} warning(s):\n")
        for idx, warning in enumerate(warning_list, start=1):
            print(f"  {idx}. {warning}")
    print()
    print("=" * 45)
    print()

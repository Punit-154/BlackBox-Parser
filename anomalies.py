import math
from datetime import datetime


BATTERY_LOW_THRESHOLD = 20          
ALTITUDE_DROP_THRESHOLD = 10.0      
ROLL_LIMIT_DEG = 45.0               
PITCH_LIMIT_DEG = 45.0              


def _ts_to_time_str(timestamp: float) -> str:
    
    return datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")


def check_low_battery(data: dict, threshold: int = BATTERY_LOW_THRESHOLD) -> list[str]:
    
    warnings_list = []
    already_warned = False

    for entry in data["sys_status"]:
        remaining = entry.get("battery_remaining", -1)

        
        if remaining < 0:
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
    warnings_list = []
    records = data["global_position"]

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
    
    warnings_list = []

    for entry in data["attitude"]:
        roll_deg = abs(math.degrees(entry["roll"]))
        pitch_deg = abs(math.degrees(entry["pitch"]))
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


def run_all_checks(data: dict) -> list[str]:
    
    all_warnings = []
    all_warnings.extend(check_low_battery(data))
    all_warnings.extend(check_altitude_drop(data))
    all_warnings.extend(check_excessive_attitude(data))
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

import math


def _format_duration(seconds: float) -> str:
    if seconds <= 0:
        return "0m 0s"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    return f"{minutes}m {secs}s"


def _compute_speed_from_global_position(global_position: list) -> list:
    speeds = []
    for entry in global_position:
        vx = entry.get("vx", 0.0)
        vy = entry.get("vy", 0.0)
        speed = math.sqrt(vx ** 2 + vy ** 2)
        speeds.append(speed)
    return speeds


def generate_summary(data: dict) -> dict:
    
    meta = data["meta"]

    
    start = meta.get("start_time") or 0
    end = meta.get("end_time") or 0
    duration = max(end - start, 0)

    
    altitudes = [
        entry["relative_alt"]
        for entry in data["global_position"]
        if "relative_alt" in entry
    ]
    max_altitude = max(altitudes) if altitudes else 0.0

    
    
    gps_speeds = [entry["speed"] for entry in data["gps_raw"] if "speed" in entry]
    global_speeds = _compute_speed_from_global_position(data["global_position"])

    all_speeds = gps_speeds if gps_speeds else global_speeds

    avg_speed = sum(all_speeds) / len(all_speeds) if all_speeds else 0.0
    max_speed = max(all_speeds) if all_speeds else 0.0

    
    battery_values = [
        entry["battery_remaining"]
        for entry in data["sys_status"]
        if entry.get("battery_remaining", -1) >= 0
    ]
    battery_start = battery_values[0] if battery_values else -1
    battery_end = battery_values[-1] if battery_values else -1
    battery_used = (battery_start - battery_end) if (battery_start >= 0 and battery_end >= 0) else 0

    
    gps_count = len(data["gps_raw"]) + len(data["global_position"])
    attitude_count = len(data["attitude"])

    stats = {
        "duration_seconds": duration,
        "duration_formatted": _format_duration(duration),
        "total_messages": meta["total_messages"],
        "parsed_messages": meta["parsed_messages"],
        "max_altitude": round(max_altitude, 2),
        "avg_speed": round(avg_speed, 2),
        "max_speed": round(max_speed, 2),
        "battery_start": battery_start,
        "battery_end": battery_end,
        "battery_used": battery_used,
        "gps_sample_count": gps_count,
        "attitude_sample_count": attitude_count,
    }

    return stats


def print_summary(stats: dict) -> None:
    
    print()
    print("=" * 45)
    print("              FLIGHT SUMMARY")
    print("=" * 45)
    print()

    print(f"  Duration           : {stats['duration_formatted']}")
    print(f"  Total Messages     : {stats['total_messages']}")
    print(f"  Parsed Messages    : {stats['parsed_messages']}")
    print()

    print(f"  Max Altitude       : {stats['max_altitude']} m")
    print(f"  Average Speed      : {stats['avg_speed']} m/s")
    print(f"  Max Speed          : {stats['max_speed']} m/s")
    print()

    if stats["battery_start"] >= 0:
        print(f"  Battery Start      : {stats['battery_start']}%")
        print(f"  Battery End        : {stats['battery_end']}%")
        print(f"  Battery Used       : {stats['battery_used']}%")
    else:
        print("  Battery Data       : Not available")
    print()

    print(f"  GPS Samples        : {stats['gps_sample_count']}")
    print(f"  Attitude Samples   : {stats['attitude_sample_count']}")

    print()
    print("=" * 45)
    print()

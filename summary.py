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


def _compute_speed_from_position(position: list) -> list:
    """Compute ground speed from position vx/vy components.

    Safely handles None values in vx/vy fields (common with .bin logs
    where position data may be empty or partially populated).
    """
    speeds = []
    for entry in position:
        vx = entry.get("vx")
        vy = entry.get("vy")
        # Skip entries where velocity data is missing
        if vx is None or vy is None:
            continue
        speed = math.sqrt(vx ** 2 + vy ** 2)
        speeds.append(speed)
    return speeds


def generate_summary(data: dict) -> dict:
    
    meta = data["meta"]

    
    start = meta.get("start_time") or 0
    end = meta.get("end_time") or 0
    duration = max(end - start, 0)

    # --- Max altitude (from position data, if available) ---
    # Filter out None values — .bin logs may have empty position list
    altitudes = [
        entry["relative_alt"]
        for entry in data["position"]
        if entry.get("relative_alt") is not None
    ]
    max_altitude = max(altitudes) if altitudes else 0.0

    # --- Speed ---
    # Prefer GPS-derived speed; fall back to computing from position vx/vy.
    # Filter out None values for safety.
    gps_speeds = [
        entry["speed"]
        for entry in data["gps"]
        if entry.get("speed") is not None
    ]
    global_speeds = _compute_speed_from_position(data["position"])

    all_speeds = gps_speeds if gps_speeds else global_speeds

    avg_speed = sum(all_speeds) / len(all_speeds) if all_speeds else 0.0
    max_speed = max(all_speeds) if all_speeds else 0.0

    # --- Battery ---
    # Filter out None and negative values — .bin logs set battery_remaining=None
    battery_values = [
        entry["battery_remaining"]
        for entry in data["battery"]
        if entry.get("battery_remaining") is not None and entry["battery_remaining"] >= 0
    ]
    battery_start = battery_values[0] if battery_values else -1
    battery_end = battery_values[-1] if battery_values else -1
    battery_used = (battery_start - battery_end) if (battery_start >= 0 and battery_end >= 0) else 0

    
    gps_count = len(data["gps"]) + len(data["position"])
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

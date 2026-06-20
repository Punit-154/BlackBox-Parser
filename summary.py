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
def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on the earth."""
    R = 6371000                             
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0)**2 +        math.cos(phi_1) * math.cos(phi_2) *        math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
def _compute_speed_from_position(position: list) -> list:
    """Compute ground speed from position vx/vy components.
    Safely handles None values in vx/vy fields (common with .bin logs
    where position data may be empty or partially populated).
    """
    speeds = []
    for entry in position:
        vx = entry.get("vx")
        vy = entry.get("vy")
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
    altitudes = [
        entry["relative_alt"]
        for entry in data["position"]
        if entry.get("relative_alt") is not None
    ]
    max_altitude = max(altitudes) if altitudes else 0.0
    gps_speeds = [
        entry["speed"]
        for entry in data["gps"]
        if entry.get("speed") is not None
    ]
    global_speeds = _compute_speed_from_position(data["position"])
    all_speeds = gps_speeds if gps_speeds else global_speeds
    avg_speed = sum(all_speeds) / len(all_speeds) if all_speeds else 0.0
    max_speed = max(all_speeds) if all_speeds else 0.0
    battery_values = [
        entry["battery_remaining"]
        for entry in data["battery"]
        if entry.get("battery_remaining") is not None and entry["battery_remaining"] >= 0
    ]
    battery_start = battery_values[0] if battery_values else -1
    battery_end = battery_values[-1] if battery_values else -1
    battery_used = (battery_start - battery_end) if (battery_start >= 0 and battery_end >= 0) else 0
    total_distance = 0.0
    max_displacement = 0.0
    if data["gps"]:
        home_lat = data["gps"][0]["lat"]
        home_lon = data["gps"][0]["lon"]
        for i in range(1, len(data["gps"])):
            prev = data["gps"][i-1]
            curr = data["gps"][i]
            dist = _haversine(prev["lat"], prev["lon"], curr["lat"], curr["lon"])
            total_distance += dist
            disp = _haversine(home_lat, home_lon, curr["lat"], curr["lon"])
            if disp > max_displacement:
                max_displacement = disp
    peak_climb_rate = 0.0
    peak_descent_rate = 0.0
    valid_pos = [entry for entry in data["position"] if entry.get("relative_alt") is not None]
    if len(valid_pos) >= 2:
        for i in range(1, len(valid_pos)):
            prev = valid_pos[i-1]
            curr = valid_pos[i]
            dt = curr["timestamp"] - prev["timestamp"]
            if dt > 0:
                dz = curr["relative_alt"] - prev["relative_alt"]
                rate = dz / dt
                if rate > peak_climb_rate:
                    peak_climb_rate = rate
                if rate < peak_descent_rate:
                    peak_descent_rate = rate
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
        "total_distance": round(total_distance, 2),
        "max_displacement": round(max_displacement, 2),
        "peak_climb_rate": round(peak_climb_rate, 2),
        "peak_descent_rate": round(abs(peak_descent_rate), 2),
        "battery_start": battery_start,
        "battery_end": battery_end,
        "battery_used": battery_used,
        "gps_sample_count": gps_count,
        "attitude_sample_count": attitude_count,
        "events": data.get("events", []),
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
    print(f"  Total Distance     : {stats['total_distance']} m")
    print(f"  Max Displacement   : {stats['max_displacement']} m")
    print(f"  Peak Climb Rate    : {stats['peak_climb_rate']} m/s")
    print(f"  Peak Descent Rate  : {stats['peak_descent_rate']} m/s")
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
    events = stats.get("events", [])
    if events:
        print("  FLIGHT EVENTS TIMELINE:")
        events.sort(key=lambda e: e["timestamp"])
        for ev in events:
            time_str = ev["datetime"] or f"T+{ev['timestamp']:.0f}s"
            if time_str and " " in time_str:
                time_str = time_str.split(" ")[1]
            print(f"    [{time_str}] {ev['name']}")
        print()
    print("=" * 45)
    print()

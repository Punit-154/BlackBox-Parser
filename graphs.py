import os
import math
from datetime import datetime
import matplotlib
matplotlib.use("Agg")  
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def _ensure_dir(dirpath: str) -> None:
    
    os.makedirs(dirpath, exist_ok=True)


def _timestamps_to_datetimes(records: list) -> list:
    """Convert timestamp fields to datetime objects for plotting.

    Safely skips records with None or boot-relative timestamps
    (common with DataFlash .bin logs).
    """
    result = []
    for r in records:
        ts = r.get("timestamp")
        if ts is None or ts < 946684800:  # _EPOCH_YEAR_2000
            continue
        result.append(datetime.fromtimestamp(ts))
    return result


def _filter_valid_records(records: list, required_field: str) -> list:
    """Return only records where *required_field* exists and is not None."""
    return [r for r in records if r.get(required_field) is not None]


def _apply_style(ax, title: str, xlabel: str, ylabel: str) -> None:
    
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(fontsize=9)

    
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")


def generate_altitude_graph(data: dict, output_dir: str) -> str | None:
    """Generate altitude vs time graph from position data."""
    records = _filter_valid_records(data["position"], "relative_alt")
    if not records:
        print("[WARN] No altitude data available for graph.")
        return None

    times = _timestamps_to_datetimes(records)
    altitudes = [r["relative_alt"] for r in records]

    # Ensure times and altitudes are aligned after filtering
    if len(times) != len(altitudes):
        min_len = min(len(times), len(altitudes))
        times = times[:min_len]
        altitudes = altitudes[:min_len]

    if not times:
        print("[WARN] No valid timestamps for altitude graph.")
        return None

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(times, altitudes, color="#2196F3", linewidth=1.2, label="Relative Altitude")
    ax.fill_between(times, altitudes, alpha=0.15, color="#2196F3")
    _apply_style(ax, "Altitude vs Time", "Time", "Altitude (m)")

    fig.tight_layout()
    filepath = os.path.join(output_dir, "altitude_vs_time.png")
    fig.savefig(filepath, dpi=150)
    plt.close(fig)

    print(f"[OK] Graph saved -> {filepath}")
    return filepath


def generate_battery_graph(data: dict, output_dir: str) -> str | None:
    """Generate battery level vs time graph.

    Safely filters out records where battery_remaining is None
    (common with DataFlash .bin logs).
    """
    records = [
        r for r in data["battery"]
        if r.get("battery_remaining") is not None and r["battery_remaining"] >= 0
    ]
    if not records:
        print("[WARN] No battery data available for graph.")
        return None

    times = _timestamps_to_datetimes(records)
    battery = [r["battery_remaining"] for r in records]

    if len(times) != len(battery):
        min_len = min(len(times), len(battery))
        times = times[:min_len]
        battery = battery[:min_len]

    if not times:
        print("[WARN] No valid timestamps for battery graph.")
        return None

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(times, battery, color="#4CAF50", linewidth=1.2, label="Battery %")
    ax.fill_between(times, battery, alpha=0.15, color="#4CAF50")
    ax.set_ylim(0, 105)
    _apply_style(ax, "Battery Level vs Time", "Time", "Battery Remaining (%)")

    fig.tight_layout()
    filepath = os.path.join(output_dir, "battery_vs_time.png")
    fig.savefig(filepath, dpi=150)
    plt.close(fig)

    print(f"[OK] Graph saved -> {filepath}")
    return filepath


def generate_speed_graph(data: dict, output_dir: str) -> str | None:
    """Generate ground speed vs time graph.

    Prefers GPS data; falls back to computing speed from position vx/vy.
    Safely handles None values in speed and velocity fields.
    """
    if data["gps"]:
        # Filter out records where speed is None
        records = _filter_valid_records(data["gps"], "speed")
        if records:
            speeds = [r["speed"] for r in records]
            source = "GPS"
        else:
            records = []
            speeds = []
            source = None

    if not records and data["position"]:
        # Fall back to position data — compute speed from vx/vy
        valid = [
            r for r in data["position"]
            if r.get("vx") is not None and r.get("vy") is not None
        ]
        if valid:
            records = valid
            speeds = [math.sqrt(r["vx"] ** 2 + r["vy"] ** 2) for r in records]
            source = "POSITION"

    if not records:
        print("[WARN] No speed data available for graph.")
        return None

    times = _timestamps_to_datetimes(records)

    if len(times) != len(speeds):
        min_len = min(len(times), len(speeds))
        times = times[:min_len]
        speeds = speeds[:min_len]

    if not times:
        print("[WARN] No valid timestamps for speed graph.")
        return None

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(times, speeds, color="#FF9800", linewidth=1.2, label=f"Speed ({source})")
    ax.fill_between(times, speeds, alpha=0.15, color="#FF9800")
    _apply_style(ax, "Ground Speed vs Time", "Time", "Speed (m/s)")

    fig.tight_layout()
    filepath = os.path.join(output_dir, "speed_vs_time.png")
    fig.savefig(filepath, dpi=150)
    plt.close(fig)

    print(f"[OK] Graph saved -> {filepath}")
    return filepath


def generate_attitude_graph(data: dict, output_dir: str) -> str | None:
    """Generate roll and pitch vs time graph.

    Safely handles None values in roll/pitch fields (should not normally
    be None, but defensive coding for robustness).
    """
    records = [
        r for r in data["attitude"]
        if r.get("roll") is not None and r.get("pitch") is not None
    ]
    if not records:
        print("[WARN] No attitude data available for graph.")
        return None

    times = _timestamps_to_datetimes(records)
    roll_deg = [math.degrees(r["roll"]) for r in records]
    pitch_deg = [math.degrees(r["pitch"]) for r in records]

    if len(times) != len(roll_deg):
        min_len = min(len(times), len(roll_deg))
        times = times[:min_len]
        roll_deg = roll_deg[:min_len]
        pitch_deg = pitch_deg[:min_len]

    if not times:
        print("[WARN] No valid timestamps for attitude graph.")
        return None

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(times, roll_deg, color="blue", linewidth=1.2, label="Roll (+Right / -Left)")
    ax.plot(times, pitch_deg, color="red", linewidth=1.2, label="Pitch (+Up / -Down)")
    ax.fill_between(times, roll_deg, alpha=0.10, color="blue")
    ax.fill_between(times, pitch_deg, alpha=0.10, color="red")
    _apply_style(ax, "Roll and Pitch vs Time", "Time", "Angle (degrees)")

    fig.tight_layout()
    filepath = os.path.join(output_dir, "attitude_vs_time.png")
    fig.savefig(filepath, dpi=150)
    plt.close(fig)

    print(f"[OK] Graph saved -> {filepath}")
    return filepath


def generate_all_graphs(data: dict, output_dir: str = "output/graphs") -> list[str]:

    _ensure_dir(output_dir)
    print(f"\n[INFO] Generating graphs in: {output_dir}/")

    generated = []
    for generator in (generate_altitude_graph, generate_battery_graph, generate_speed_graph, generate_attitude_graph):
        path = generator(data, output_dir)
        if path:
            generated.append(path)

    print(f"[INFO] Generated {len(generated)} graph(s).\n")
    return generated

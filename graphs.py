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
    return [datetime.fromtimestamp(r["timestamp"]) for r in records]


def _apply_style(ax, title: str, xlabel: str, ylabel: str) -> None:
    
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(fontsize=9)

    
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")


def generate_altitude_graph(data: dict, output_dir: str) -> str | None:
    
    records = data["global_position"]
    if not records:
        print("[WARN] No altitude data available for graph.")
        return None

    times = _timestamps_to_datetimes(records)
    altitudes = [r["relative_alt"] for r in records]

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
    
    records = [r for r in data["sys_status"] if r.get("battery_remaining", -1) >= 0]
    if not records:
        print("[WARN] No battery data available for graph.")
        return None

    times = _timestamps_to_datetimes(records)
    battery = [r["battery_remaining"] for r in records]

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
    
    if data["gps_raw"]:
        records = data["gps_raw"]
        speeds = [r["speed"] for r in records]
        source = "GPS_RAW_INT"
    elif data["global_position"]:
        records = data["global_position"]
        speeds = [math.sqrt(r["vx"] ** 2 + r["vy"] ** 2) for r in records]
        source = "GLOBAL_POSITION_INT"
    else:
        print("[WARN] No speed data available for graph.")
        return None

    times = _timestamps_to_datetimes(records)

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
    
    records = data["attitude"]
    if not records:
        print("[WARN] No attitude data available for graph.")
        return None

    times = _timestamps_to_datetimes(records)
    roll_deg = [math.degrees(r["roll"]) for r in records]
    pitch_deg = [math.degrees(r["pitch"]) for r in records]

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

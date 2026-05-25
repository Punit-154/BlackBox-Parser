import os
import math
import pandas as pd


def _ensure_dir(dirpath: str) -> None:
    os.makedirs(dirpath, exist_ok=True)


def export_gps_csv(data: dict, output_dir: str) -> str | None:

    records = data["gps_raw"]
    if not records:
        print("[WARN] No GPS_RAW_INT data to export.")
        return None

    df = pd.DataFrame(records)
    cols = ["datetime", "lat", "lon", "alt", "speed", "satellites", "fix_type"]
    df = df[[c for c in cols if c in df.columns]]

    filepath = os.path.join(output_dir, "gps.csv")
    df.to_csv(filepath, index=False)
    print(f"[OK] Exported GPS data        -> {filepath}  ({len(df)} rows)")
    return filepath


def export_altitude_csv(data: dict, output_dir: str) -> str | None:
    
    records = data["global_position"]
    if not records:
        print("[WARN] No GLOBAL_POSITION_INT data to export.")
        return None

    df = pd.DataFrame(records)

    
    if "vx" in df.columns and "vy" in df.columns:
        df["ground_speed"] = (df["vx"] ** 2 + df["vy"] ** 2).apply(math.sqrt)

    cols = ["datetime", "lat", "lon", "alt", "relative_alt", "ground_speed", "heading"]
    df = df[[c for c in cols if c in df.columns]]

    filepath = os.path.join(output_dir, "altitude.csv")
    df.to_csv(filepath, index=False)
    print(f"[OK] Exported Altitude data   -> {filepath}  ({len(df)} rows)")
    return filepath


def export_battery_csv(data: dict, output_dir: str) -> str | None:
    
    records = data["sys_status"]
    if not records:
        print("[WARN] No SYS_STATUS data to export.")
        return None

    df = pd.DataFrame(records)
    cols = ["datetime", "voltage", "current", "battery_remaining"]
    df = df[[c for c in cols if c in df.columns]]

    filepath = os.path.join(output_dir, "battery.csv")
    df.to_csv(filepath, index=False)
    print(f"[OK] Exported Battery data    -> {filepath}  ({len(df)} rows)")
    return filepath


def export_attitude_csv(data: dict, output_dir: str) -> str | None:
    
    records = data["attitude"]
    if not records:
        print("[WARN] No ATTITUDE data to export.")
        return None

    df = pd.DataFrame(records)

    
    if "roll" in df.columns:
        df["roll_deg"] = df["roll"].apply(math.degrees).round(2)
    if "pitch" in df.columns:
        df["pitch_deg"] = df["pitch"].apply(math.degrees).round(2)
    if "yaw" in df.columns:
        df["yaw_deg"] = df["yaw"].apply(math.degrees).round(2)

    cols = [
        "datetime", "roll", "pitch", "yaw",
        "roll_deg", "pitch_deg", "yaw_deg",
        "rollspeed", "pitchspeed", "yawspeed",
    ]
    df = df[[c for c in cols if c in df.columns]]

    filepath = os.path.join(output_dir, "attitude.csv")
    df.to_csv(filepath, index=False)
    print(f"[OK] Exported Attitude data   -> {filepath}  ({len(df)} rows)")
    return filepath


def export_all(data: dict, output_dir: str = "output/csv") -> list[str]:
    
    _ensure_dir(output_dir)
    print(f"\n[INFO] Exporting CSV files to: {output_dir}/")

    exported = []
    for exporter in (export_gps_csv, export_altitude_csv, export_battery_csv, export_attitude_csv):
        path = exporter(data, output_dir)
        if path:
            exported.append(path)

    print(f"[INFO] Exported {len(exported)} CSV file(s).\n")
    return exported

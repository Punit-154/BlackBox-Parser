import os
import math
import pandas as pd


def _ensure_dir(dirpath: str) -> None:
    os.makedirs(dirpath, exist_ok=True)


def export_gps_csv(data: dict, output_dir: str) -> str | None:
    """Export GPS telemetry records to CSV.

    Works identically for both .tlog and .bin sources since
    the parser normalises GPS data into the same schema.
    """
    records = data["gps"]
    if not records:
        print("[WARN] No GPS data to export.")
        return None

    df = pd.DataFrame(records)
    cols = ["datetime", "lat", "lon", "alt", "speed", "satellites", "fix_type"]
    df = df[[c for c in cols if c in df.columns]]

    filepath = os.path.join(output_dir, "gps.csv")
    df.to_csv(filepath, index=False)
    print(f"[OK] Exported GPS data        -> {filepath}  ({len(df)} rows)")
    return filepath


def export_altitude_csv(data: dict, output_dir: str) -> str | None:
    """Export position / altitude records to CSV.

    Note: For .bin logs, the position list will typically be empty
    because DataFlash logs lack a GLOBAL_POSITION_INT equivalent.
    """
    records = data["position"]
    if not records:
        print("[WARN] No position data to export.")
        return None

    df = pd.DataFrame(records)

    # Compute ground speed from vx/vy if both are available and not None
    if "vx" in df.columns and "vy" in df.columns:
        # Replace None with NaN so math works, then compute
        vx = pd.to_numeric(df["vx"], errors="coerce")
        vy = pd.to_numeric(df["vy"], errors="coerce")
        df["ground_speed"] = (vx ** 2 + vy ** 2).apply(
            lambda v: math.sqrt(v) if pd.notna(v) else None
        )

    cols = ["datetime", "lat", "lon", "alt", "relative_alt", "ground_speed", "heading"]
    df = df[[c for c in cols if c in df.columns]]

    filepath = os.path.join(output_dir, "altitude.csv")
    df.to_csv(filepath, index=False)
    print(f"[OK] Exported Altitude data   -> {filepath}  ({len(df)} rows)")
    return filepath


def export_battery_csv(data: dict, output_dir: str) -> str | None:
    """Export battery telemetry records to CSV.

    Handles None values in battery_remaining (common with .bin logs
    where DataFlash BAT messages don't include this field).
    """
    records = data["battery"]
    if not records:
        print("[WARN] No battery data to export.")
        return None

    df = pd.DataFrame(records)
    cols = ["datetime", "voltage", "current", "battery_remaining"]
    df = df[[c for c in cols if c in df.columns]]

    filepath = os.path.join(output_dir, "battery.csv")
    df.to_csv(filepath, index=False)
    print(f"[OK] Exported Battery data    -> {filepath}  ({len(df)} rows)")
    return filepath


def export_attitude_csv(data: dict, output_dir: str) -> str | None:
    """Export attitude records to CSV.

    Safely handles None values in roll/pitch/yaw and angular rates.
    For .bin logs, rollspeed/pitchspeed/yawspeed will be None.
    """
    records = data["attitude"]
    if not records:
        print("[WARN] No attitude data to export.")
        return None

    df = pd.DataFrame(records)

    # Convert radians to degrees — safely handle None values
    for field in ("roll", "pitch", "yaw"):
        if field in df.columns:
            df[f"{field}_deg"] = df[field].apply(
                lambda v: round(math.degrees(v), 2) if v is not None else None
            )

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

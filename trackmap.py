import os
import folium
from folium import plugins


def _extract_gps_coords(data: dict) -> list[tuple[float, float]]:
    """Extract valid (lat, lon) pairs from GPS or position data.

    Prioritizes GPS data (more reliable). Falls back to position data
    if GPS is empty. Filters out any entries with None coordinates.
    """
    records = data["gps"] if data["gps"] else data["position"]

    coords = []
    for r in records:
        lat = r.get("lat")
        lon = r.get("lon")
        if lat is not None and lon is not None:
            coords.append((lat, lon))

    return coords


def _get_center(coords: list[tuple[float, float]]) -> tuple[float, float]:
    """Calculate the center point of all coordinates.

    Uses simple arithmetic mean. For a flight that spans a small area,
    this is accurate enough. For flights spanning huge distances,
    a spherical mean would be more precise, but overkill here.
    """
    if not coords:
        return (0.0, 0.0)

    avg_lat = sum(c[0] for c in coords) / len(coords)
    avg_lon = sum(c[1] for c in coords) / len(coords)
    return (avg_lat, avg_lon)


def _add_speed_color(coords: list[tuple[float, float]], data: dict) -> list:
    """Create color-coded line segments based on speed.

    Returns a list of GeoJson style dictionaries, one per segment.
    Color mapping: green (slow) -> yellow (medium) -> orange (fast) -> red (very fast).
    """
    gps_records = data["gps"] if data["gps"] else data["position"]

    speeds = []
    for r in gps_records:
        s = r.get("speed")
        if s is None and r.get("vx") is not None and r.get("vy") is not None:
            import math
            s = math.sqrt(r["vx"] ** 2 + r["vy"] ** 2)
        speeds.append(s if s is not None else 0.0)

    if not speeds:
        return []

    max_speed = max(speeds) if speeds else 1.0
    if max_speed == 0:
        max_speed = 1.0

    colors = []
    for s in speeds:
        ratio = s / max_speed
        if ratio < 0.25:
            color = "#4CAF50"
        elif ratio < 0.50:
            color = "#FFC107"
        elif ratio < 0.75:
            color = "#FF9800"
        else:
            color = "#F44336"
        colors.append(color)

    return colors


def generate_track_map(data: dict, output_dir: str = "output") -> str | None:
    """Generate an interactive HTML map showing the drone's flight path.

    Creates a Leaflet.js map (via folium) with:
    - Color-coded flight path (green=slow, red=fast)
    - Green marker at takeoff point
    - Red marker at landing point
    - Popup tooltips showing coordinates on hover

    Returns the filepath to the generated HTML file, or None if
    no valid GPS data is available.
    """
    coords = _extract_gps_coords(data)

    if len(coords) < 2:
        print("[WARN] Need at least 2 GPS points to draw a track map.")
        return None

    center = _get_center(coords)

    m = folium.Map(
        location=center,
        zoom_start=16,
        tiles="OpenStreetMap",
    )

    speed_colors = _add_speed_color(coords, data)

    for i in range(len(coords) - 1):
        color = speed_colors[i] if i < len(speed_colors) else "#2196F3"
        segment = [coords[i], coords[i + 1]]

        folium.PolyLine(
            segment,
            color=color,
            weight=4,
            opacity=0.8,
            tooltip=f"Segment {i + 1}",
        ).add_to(m)

    folium.Marker(
        coords[0],
        popup="Takeoff",
        tooltip="Takeoff Point",
        icon=folium.Icon(color="green", icon="play", prefix="fa"),
    ).add_to(m)

    folium.Marker(
        coords[-1],
        popup="Landing",
        tooltip="Landing Point",
        icon=folium.Icon(color="red", icon="stop", prefix="fa"),
    ).add_to(m)

    plugins.Fullscreen().add_to(m)
    plugins.MousePosition().add_to(m)

    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "flight_track.html")
    m.save(filepath)

    print(f"[OK] Flight track map saved -> {filepath}")
    print(f"     Open in browser to view interactive map.")
    return filepath

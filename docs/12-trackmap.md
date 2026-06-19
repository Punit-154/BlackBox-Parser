# trackmap.py — GPS Flight Track Visualization

## What It Does
Generates an interactive HTML map showing the drone's flight path using Leaflet.js (via the folium library). The map is color-coded by speed and includes takeoff/landing markers.

## File Location
`trackmap.py` (project root)

## Output
`output/flight_track.html` — an interactive map you can open in any browser.

## What the Map Shows
1. **Flight path** — a polyline connecting all GPS points
2. **Speed coloring** — green (slow) -> yellow -> orange -> red (fast)
3. **Takeoff marker** — green play icon at the first GPS point
4. **Landing marker** — red stop icon at the last GPS point
5. **Fullscreen button** — expand to fill the screen
6. **Mouse position** — shows coordinates as you move the mouse

---

## Line-by-Line Code Explanation

### Import Section (Lines 1-3)
```python
import os
import folium
from folium import plugins
```
- `os` — for directory creation and file path handling
- `folium` — Python library that generates Leaflet.js maps as HTML files
- `plugins` — folium extras like fullscreen button and mouse position display

---

### _extract_gps_coords(data) (Lines 6-20)
```python
def _extract_gps_coords(data: dict) -> list[tuple[float, float]]:
```

**Purpose:** Get a list of (latitude, longitude) pairs from the data dict.

**Line-by-line:**
```python
records = data["gps"] if data["gps"] else data["position"]
```
- Prioritizes GPS data (more accurate, has speed info)
- Falls back to position data if GPS is empty (happens with .bin logs)

```python
coords = []
for r in records:
    lat = r.get("lat")
    lon = r.get("lon")
    if lat is not None and lon is not None:
        coords.append((lat, lon))
```
- Loops through each record
- Uses `.get()` instead of `[]` to avoid KeyError if field is missing
- Only adds coordinates where BOTH lat and lon are present (filters out None values)
- Returns a list of tuples: `[(28.6139, 77.2090), (28.6140, 77.2091), ...]`

**Why this matters:** .bin logs may have incomplete GPS data. Filtering None prevents crashes.

---

### _get_center(coords) (Lines 23-35)
```python
def _get_center(coords: list[tuple[float, float]]) -> tuple[float, float]:
```

**Purpose:** Calculate the center point of the map so it opens focused on the flight area.

**Line-by-line:**
```python
if not coords:
    return (0.0, 0.0)
```
- Empty list → default to (0, 0) which shows the Atlantic Ocean
- This is a fallback; in practice, we check for empty coords before calling this

```python
avg_lat = sum(c[0] for c in coords) / len(coords)
avg_lon = sum(c[1] for c in coords) / len(coords)
return (avg_lat, avg_lon)
```
- Simple arithmetic mean of all latitudes and longitudes
- `c[0]` is latitude, `c[1]` is longitude (tuple indexing)
- For small-area flights, this is accurate enough

**Interview point:** For flights spanning hundreds of kilometers, a spherical mean would be more precise. But for drone flights (typically < 5km), arithmetic mean is fine.

---

### _add_speed_color(coords, data) (Lines 38-75)
```python
def _add_speed_color(coords: list[tuple[float, float]], data: dict) -> list:
```

**Purpose:** Assign a color to each line segment based on the drone's speed at that point.

**Line-by-line:**
```python
gps_records = data["gps"] if data["gps"] else data["position"]
```
- Same priority logic as `_extract_gps_coords`

```python
speeds = []
for r in gps_records:
    s = r.get("speed")
    if s is None and r.get("vx") is not None and r.get("vy") is not None:
        import math
        s = math.sqrt(r["vx"] ** 2 + r["vy"] ** 2)
    speeds.append(s if s is not None else 0.0)
```
- Tries to get speed directly from GPS (preferred)
- If speed is None (happens with .bin logs), computes from velocity components: `speed = sqrt(vx² + vy²)`
- If both are None, defaults to 0.0

```python
if not speeds:
    return []

max_speed = max(speeds) if speeds else 1.0
if max_speed == 0:
    max_speed = 1.0
```
- Empty list → return empty (no colors to assign)
- `max_speed = 1.0` prevents division by zero when drone is stationary

```python
colors = []
for s in speeds:
    ratio = s / max_speed
    if ratio < 0.25:
        color = "#4CAF50"    # Green - slow
    elif ratio < 0.50:
        color = "#FFC107"    # Yellow - medium
    elif ratio < 0.75:
        color = "#FF9800"    # Orange - fast
    else:
        color = "#F44336"    # Red - very fast
    colors.append(color)
```
- Normalizes speed to 0.0-1.0 range (ratio of current speed to max speed)
- Maps ratio to 4 color buckets
- Returns list of hex color strings

**Interview point:** This is a simple quantile-based color mapping. More sophisticated approaches could use continuous color gradients, but 4 buckets are visually clear and easy to understand.

---

### generate_track_map(data, output_dir) (Lines 78-135)
```python
def generate_track_map(data: dict, output_dir: str = "output") -> str | None:
```

**Purpose:** The main function that creates the interactive HTML map.

**Line-by-line:**
```python
coords = _extract_gps_coords(data)

if len(coords) < 2:
    print("[WARN] Need at least 2 GPS points to draw a track map.")
    return None
```
- Extracts coordinates
- Needs at least 2 points to draw a line (1 point = just a dot, not useful)

```python
center = _get_center(coords)
```
- Calculates map center

```python
m = folium.Map(
    location=center,
    zoom_start=16,
    tiles="OpenStreetMap",
)
```
- Creates a new folium Map object
- `location=center` — centers the map on the flight area
- `zoom_start=16` — close zoom level (good for drone flights)
- `tiles="OpenStreetMap"` — uses free OpenStreetMap tiles (no API key needed)

```python
speed_colors = _add_speed_color(coords, data)
```
- Gets color for each segment

```python
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
```
- Loops through consecutive pairs of coordinates
- Creates a line segment between each pair
- `weight=4` — line thickness in pixels
- `opacity=0.8` — slightly transparent so map tiles show through
- `tooltip` — text that appears when hovering over the line

```python
folium.Marker(
    coords[0],
    popup="Takeoff",
    tooltip="Takeoff Point",
    icon=folium.Icon(color="green", icon="play", prefix="fa"),
).add_to(m)
```
- Green marker at the first GPS point (takeoff)
- `popup` — text shown when clicking the marker
- `tooltip` — text shown when hovering
- `icon="play"` with `prefix="fa"` — uses Font Awesome play icon

```python
folium.Marker(
    coords[-1],
    popup="Landing",
    tooltip="Landing Point",
    icon=folium.Icon(color="red", icon="stop", prefix="fa"),
).add_to(m)
```
- Red marker at the last GPS point (landing)
- Uses Font Awesome stop icon

```python
plugins.Fullscreen().add_to(m)
plugins.MousePosition().add_to(m)
```
- Adds a fullscreen button (top-right corner)
- Adds mouse position display (shows lat/lon as you move the mouse)

```python
os.makedirs(output_dir, exist_ok=True)
filepath = os.path.join(output_dir, "flight_track.html")
m.save(filepath)
```
- Creates output directory if it doesn't exist
- Saves the map as an HTML file

```python
print(f"[OK] Flight track map saved -> {filepath}")
print(f"     Open in browser to view interactive map.")
return filepath
```
- Prints confirmation and filepath
- Returns the filepath for programmatic use

---

## Interview Points

### Q: Why use folium/Leaflet instead of matplotlib?
"Matplotlib generates static images. Folium generates interactive HTML maps where users can zoom, pan, and click markers. For a flight track, interactivity is much more useful — you can zoom into specific areas of the flight."

### Q: How does the speed coloring work?
"Each line segment gets a color based on the drone's speed at that point. I normalize speed to a 0-1 ratio (current speed / max speed), then map to 4 color buckets: green (< 25%), yellow (< 50%), orange (< 75%), red (> 75%). This gives a quick visual indication of where the drone was fast or slow."

### Q: What if GPS data is missing?
"The function falls back to position data, which is reconstructed from GPS in the parser's post-processing step. If both are empty, it returns None and prints a warning. Every coordinate is checked for None before use."

### Q: Why OpenStreetMap tiles?
"OpenStreetMap is free, requires no API key, and has good coverage worldwide. For a professional version, you could offer satellite imagery tiles, but that would require a Mapbox or Google Maps API key."

### Q: How would you extend this?
"Three options: (1) Add a heatmap layer showing time spent in each area, (2) Add altitude-colored markers showing height at each point, (3) Export to GeoJSON for use in GIS tools like QGIS."

"""Shared pytest fixtures for BlackBox-Parser tests.
All fixtures return synthetic data — no real log files or pymavlink required.
"""
import math
import os
import sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
BASE_TS = 1700000000.0
@pytest.fixture
def empty_data():
    """Standard data dict with every key present but empty lists."""
    return {
        "gps": [],
        "position": [],
        "battery": [],
        "attitude": [],
        "events": [],
        "meta": {
            "filepath": "/fake/path/test.tlog",
            "total_messages": 0,
            "parsed_messages": 0,
            "start_time": None,
            "end_time": None,
        },
    }
@pytest.fixture
def sample_data():
    """Realistic 30-second drone flight with all data categories populated.
    GPS coords hover around New Delhi (28.6139, 77.2090).
    Altitude climbs from 0 → ~50 m then descends.
    Speed varies 0-15 m/s.
    Battery drains 95 → 85 %.
    Roll/pitch within ±0.2 rad.
    Two events: Armed and Mode AUTO.
    """
    gps = []
    position = []
    battery = []
    attitude = []
    for i in range(10):
        t = BASE_TS + i * 3                                
        alt_curve = [0, 10, 25, 40, 50, 48, 40, 30, 15, 5]
        speed_curve = [0, 5, 8, 12, 15, 14, 10, 8, 5, 2]
        batt_curve = [95, 94, 93, 92, 91, 90, 89, 88, 87, 85]
        roll_curve = [0.0, 0.05, 0.1, 0.15, 0.1, -0.05, -0.1, -0.15, -0.05, 0.0]
        pitch_curve = [0.0, 0.1, 0.15, 0.1, 0.05, 0.0, -0.05, -0.1, -0.15, -0.1]
        gps.append({
            "timestamp": t,
            "datetime": "2023-11-14 22:13:20",
            "lat": 28.6139 + i * 0.0001,
            "lon": 77.2090 + i * 0.0001,
            "alt": alt_curve[i] + 200,        
            "speed": speed_curve[i],
            "satellites": 12,
            "fix_type": 3,
        })
        position.append({
            "timestamp": t,
            "datetime": "2023-11-14 22:13:20",
            "lat": 28.6139 + i * 0.0001,
            "lon": 77.2090 + i * 0.0001,
            "alt": alt_curve[i] + 200,
            "relative_alt": float(alt_curve[i]),
            "vx": speed_curve[i] * 0.7,
            "vy": speed_curve[i] * 0.7,
            "vz": 0.5 if i < 5 else -0.5,
            "heading": 90.0 + i * 5,
        })
        battery.append({
            "timestamp": t,
            "datetime": "2023-11-14 22:13:20",
            "voltage": 12.6 - i * 0.05,
            "current": 8.0 + i * 0.3,
            "battery_remaining": batt_curve[i],
        })
        attitude.append({
            "timestamp": t,
            "datetime": "2023-11-14 22:13:20",
            "roll": roll_curve[i],
            "pitch": pitch_curve[i],
            "yaw": math.radians(90 + i * 5),
            "rollspeed": 0.01,
            "pitchspeed": 0.01,
            "yawspeed": 0.005,
        })
    events = [
        {"timestamp": BASE_TS, "datetime": "2023-11-14 22:13:20", "name": "Armed"},
        {"timestamp": BASE_TS + 5, "datetime": "2023-11-14 22:13:25", "name": "Mode AUTO"},
    ]
    return {
        "gps": gps,
        "position": position,
        "battery": battery,
        "attitude": attitude,
        "events": events,
        "meta": {
            "filepath": "/fake/path/test.tlog",
            "total_messages": 100,
            "parsed_messages": 42,
            "start_time": BASE_TS,
            "end_time": BASE_TS + 27,                              
        },
    }
@pytest.fixture
def low_battery_data(empty_data):
    """Battery entries that cross the default 20 % threshold."""
    empty_data["battery"] = [
        {"timestamp": BASE_TS,     "battery_remaining": 25, "voltage": 12.0, "current": 5.0},
        {"timestamp": BASE_TS + 5, "battery_remaining": 18, "voltage": 11.5, "current": 6.0},
        {"timestamp": BASE_TS + 10, "battery_remaining": 12, "voltage": 11.0, "current": 7.0},
        {"timestamp": BASE_TS + 15, "battery_remaining": 8,  "voltage": 10.5, "current": 8.0},
    ]
    empty_data["position"] = []
    empty_data["attitude"] = []
    return empty_data
@pytest.fixture
def altitude_drop_data(empty_data):
    """Position entries with a 15 m sudden drop in the middle."""
    empty_data["position"] = [
        {"timestamp": BASE_TS,      "relative_alt": 50.0},
        {"timestamp": BASE_TS + 3,  "relative_alt": 52.0},
        {"timestamp": BASE_TS + 6,  "relative_alt": 55.0},
        {"timestamp": BASE_TS + 9,  "relative_alt": 40.0},              
        {"timestamp": BASE_TS + 12, "relative_alt": 38.0},
    ]
    empty_data["battery"] = []
    empty_data["attitude"] = []
    return empty_data
@pytest.fixture
def excessive_attitude_data(empty_data):
    """Attitude entries with extreme roll value (7.0 rad ≈ 401°)."""
    empty_data["attitude"] = [
        {"timestamp": BASE_TS,     "roll": 0.1,  "pitch": 0.1},
        {"timestamp": BASE_TS + 3, "roll": 7.0,  "pitch": 0.1},               
        {"timestamp": BASE_TS + 6, "roll": 0.1,  "pitch": 7.0},                
    ]
    empty_data["battery"] = []
    empty_data["position"] = []
    return empty_data
@pytest.fixture
def bin_style_data(empty_data):
    """Data mimicking .bin log quirks: None battery_remaining, boot-relative timestamps."""
    empty_data["battery"] = [
        {"timestamp": 100.0,  "voltage": 12.6, "current": 5.0, "battery_remaining": None},
        {"timestamp": 200.0,  "voltage": 12.4, "current": 6.0, "battery_remaining": None},
        {"timestamp": 300.0,  "voltage": 12.0, "current": 7.0, "battery_remaining": None},
    ]
    empty_data["attitude"] = [
        {"timestamp": 100.0, "roll": 0.1, "pitch": 0.1},
        {"timestamp": 200.0, "roll": 0.2, "pitch": 0.2},
    ]
    return empty_data
@pytest.fixture
def sample_config():
    """Config dict with custom (tighter) thresholds for testing."""
    return {
        "thresholds": {
            "battery_low_percent": 30,
            "altitude_drop_m": 5.0,
            "roll_limit_deg": 45.0,
            "pitch_limit_deg": 45.0,
        },
        "output": {
            "csv_dir": "output/csv",
            "graph_dir": "output/graphs",
        },
        "battery_estimation": {
            "cell_voltage_full": 4.2,
            "cell_voltage_empty": 3.5,
        },
    }

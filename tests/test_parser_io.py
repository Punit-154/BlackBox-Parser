"""Tests for parser.py — MAVLink and DataFlash parsing via mock pymavlink."""
import pytest
from unittest.mock import patch, MagicMock
import parser
@pytest.fixture
def mock_mavlink_msg():
    def _create_msg(msg_type, **kwargs):
        msg = MagicMock()
        msg.get_type.return_value = msg_type
        for k, v in kwargs.items():
            setattr(msg, k, v)
        return msg
    return _create_msg
class TestParseTlog:
    @patch("parser.mavutil.mavlink_connection")
    @patch("parser.validate_tlog_file")
    def test_parse_tlog_success(self, mock_validate, mock_conn, mock_mavlink_msg):
        mock_validate.return_value = "/fake/test.tlog"
        mock_mav = MagicMock()
        mock_conn.return_value = mock_mav
        msg1 = mock_mavlink_msg("GPS_RAW_INT", _timestamp=1700000000.0, lat=286139000, lon=772090000, alt=200000, vel=500, satellites_visible=10, fix_type=3)
        msg2 = mock_mavlink_msg("SYS_STATUS", _timestamp=1700000005.0, voltage_battery=12600, current_battery=500, battery_remaining=100)
        msg3 = mock_mavlink_msg("ATTITUDE", _timestamp=1700000010.0, roll=0.1, pitch=0.1, yaw=1.0, rollspeed=0.01, pitchspeed=0.01, yawspeed=0.01)
        msg4 = mock_mavlink_msg("STATUSTEXT", _timestamp=1700000015.0, text="Armed")
        msg5 = mock_mavlink_msg("UNKNOWN_MSG", _timestamp=1700000020.0)                    
        mock_mav.recv_match.side_effect = [msg1, msg2, msg3, msg4, msg5, None]
        data = parser.parse_tlog("test.tlog")
        assert data["meta"]["total_messages"] == 5
        assert data["meta"]["parsed_messages"] == 4
        assert len(data["gps"]) == 1
        assert data["gps"][0]["lat"] == 28.6139
        assert len(data["battery"]) == 1
        assert data["battery"][0]["voltage"] == 12.6
        assert len(data["attitude"]) == 1
        assert len(data["events"]) == 1
class TestParseBin:
    @patch("parser.mavutil.mavlink_connection")
    @patch("parser.validate_log_file")
    def test_parse_bin_success(self, mock_validate, mock_conn, mock_mavlink_msg):
        mock_validate.return_value = "/fake/test.bin"
        mock_mav = MagicMock()
        mock_conn.return_value = mock_mav
        msg1 = mock_mavlink_msg("GPS", _timestamp=1700000000.0, Lat=28.6139, Lng=77.2090, Alt=200.0, Spd=5.0, NSats=10, Status=3)
        msg2 = mock_mavlink_msg("BAT", _timestamp=1700000005.0, Volt=12.6, Curr=5.0)
        msg3 = mock_mavlink_msg("ATT", _timestamp=1700000010.0, Roll=5.73, Pitch=5.73, Yaw=90.0)          
        msg4 = mock_mavlink_msg("EV", _timestamp=1700000015.0, Id=10)        
        mock_mav.recv_match.side_effect = [msg1, msg2, msg3, msg4, None]
        data = parser.parse_bin("test.bin")
        assert data["meta"]["total_messages"] == 4
        assert data["meta"]["parsed_messages"] == 4
        assert len(data["gps"]) == 1
        assert data["gps"][0]["lat"] == 28.6139
        assert len(data["battery"]) == 1
        assert data["battery"][0]["voltage"] == 12.6
        assert len(data["attitude"]) == 1
        assert round(data["attitude"][0]["roll"], 2) == 0.10                          
        assert len(data["events"]) == 1
        assert data["events"][0]["name"] == "Armed"

import os
import tempfile
from datetime import datetime
from fpdf import FPDF
from summary import generate_summary
from graphs import (
    generate_altitude_graph,
    generate_battery_graph,
    generate_speed_graph,
    generate_attitude_graph,
    generate_power_graph,
)
from anomalies import run_all_checks
class FlightReport(FPDF):
    def __init__(self, log_filename: str):
        super().__init__()
        self.log_filename = log_filename
        self.set_auto_page_break(auto=True, margin=20)
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, f"Flight Report - {self.log_filename}", align="R")
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")
    def add_title_page(self):
        self.add_page()
        self.ln(40)
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(33, 150, 243)
        self.cell(0, 15, "Flight Analysis Report", align="C")
        self.ln(20)
        self.set_font("Helvetica", "", 14)
        self.set_text_color(80, 80, 80)
        self.cell(0, 10, f"Log File: {self.log_filename}", align="C")
        self.ln(10)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cell(0, 10, f"Generated: {now}", align="C")
        self.ln(30)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(100, 100, 100)
        lines = [
            "BlackBox-Parser",
            "Supports: .tlog (MAVLink) and .bin (ArduPilot DataFlash)",
            "",
            "This report contains:",
            "  - Flight Summary Statistics",
            "  - Telemetry Graphs (Altitude, Battery, Speed, Attitude, Power)",
            "  - Anomaly Detection Warnings",
        ]
        for line in lines:
            self.cell(0, 7, line, align="C")
            self.ln(7)
    def add_summary_section(self, stats: dict):
        self.add_page()
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(33, 33, 33)
        self.cell(0, 12, "1. Flight Summary")
        self.ln(14)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(50, 50, 50)
        sections = [
            ("Flight Duration", stats["duration_formatted"]),
            ("Total Messages", str(stats["total_messages"])),
            ("Parsed Messages", str(stats["parsed_messages"])),
        ]
        for label, value in sections:
            self._add_kv_row(label, value)
        self.ln(4)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(33, 33, 33)
        self.cell(0, 8, "Telemetry")
        self.ln(10)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(50, 50, 50)
        telemetry = [
            ("Max Altitude", f"{stats['max_altitude']} m"),
            ("Average Speed", f"{stats['avg_speed']} m/s"),
            ("Max Speed", f"{stats['max_speed']} m/s"),
            ("Total Distance", f"{stats['total_distance']} m"),
            ("Max Displacement", f"{stats['max_displacement']} m"),
            ("Peak Climb Rate", f"{stats['peak_climb_rate']} m/s"),
            ("Peak Descent Rate", f"{stats['peak_descent_rate']} m/s"),
        ]
        for label, value in telemetry:
            self._add_kv_row(label, value)
        self.ln(4)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(33, 33, 33)
        self.cell(0, 8, "Battery")
        self.ln(10)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(50, 50, 50)
        if stats["battery_start"] >= 0:
            battery = [
                ("Battery Start", f"{stats['battery_start']}%"),
                ("Battery End", f"{stats['battery_end']}%"),
                ("Battery Used", f"{stats['battery_used']}%"),
            ]
            for label, value in battery:
                self._add_kv_row(label, value)
        else:
            self._add_kv_row("Battery Data", "Not available")
        self.ln(4)
        self._add_kv_row("GPS Samples", str(stats["gps_sample_count"]))
        self._add_kv_row("Attitude Samples", str(stats["attitude_sample_count"]))
        events = stats.get("events", [])
        if events:
            self.ln(6)
            self.set_font("Helvetica", "B", 12)
            self.set_text_color(33, 33, 33)
            self.cell(0, 8, "Flight Events Timeline")
            self.ln(10)
            self.set_font("Helvetica", "", 10)
            self.set_text_color(50, 50, 50)
            sorted_events = sorted(events, key=lambda e: e["timestamp"])
            for ev in sorted_events:
                time_str = ev.get("datetime", "") or f"T+{ev['timestamp']:.0f}s"
                if time_str and " " in time_str:
                    time_str = time_str.split(" ")[1]
                self._add_kv_row(time_str, ev["name"])
    def _add_kv_row(self, label: str, value: str):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(80, 80, 80)
        self.cell(65, 7, label)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(33, 33, 33)
        self.cell(0, 7, value)
        self.ln(7)
    def add_graphs_section(self, graph_paths: list[str]):
        if not graph_paths:
            return
        self.add_page()
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(33, 33, 33)
        self.cell(0, 12, "2. Telemetry Graphs")
        self.ln(14)
        graph_labels = {
            "altitude_vs_time": "Altitude vs Time",
            "battery_vs_time": "Battery Level vs Time",
            "speed_vs_time": "Ground Speed vs Time",
            "attitude_vs_time": "Roll and Pitch vs Time",
            "power_vs_time": "Power Analysis: Voltage & Current",
        }
        for path in graph_paths:
            if not os.path.isfile(path):
                continue
            basename = os.path.splitext(os.path.basename(path))[0]
            label = graph_labels.get(basename, basename)
            if self.get_y() > 180:
                self.add_page()
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(50, 50, 50)
            self.cell(0, 8, label)
            self.ln(9)
            try:
                self.image(path, x=10, w=190)
                self.ln(6)
            except Exception:
                self.set_font("Helvetica", "I", 9)
                self.set_text_color(150, 150, 150)
                self.cell(0, 6, f"[Graph could not be embedded: {os.path.basename(path)}]")
                self.ln(8)
    def add_warnings_section(self, warnings: list[str]):
        self.add_page()
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(33, 33, 33)
        self.cell(0, 12, "3. Anomaly Detection Warnings")
        self.ln(14)
        if not warnings:
            self.set_font("Helvetica", "", 12)
            self.set_text_color(76, 175, 80)
            self.cell(0, 10, "No warnings detected. Flight looks clean!")
            self.ln(10)
            return
        self.set_font("Helvetica", "", 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, f"Found {len(warnings)} warning(s):")
        self.ln(10)
        for i, warning in enumerate(warnings, 1):
            if self.get_y() > 260:
                self.add_page()
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(244, 67, 54)
            self.cell(8, 7, f"{i}.")
            self.set_font("Helvetica", "", 10)
            self.set_text_color(50, 50, 50)
            self.multi_cell(0, 7, warning)
            self.ln(3)
def generate_report(data: dict, output_dir: str = "output", config: dict | None = None) -> str | None:
    os.makedirs(output_dir, exist_ok=True)
    stats = generate_summary(data)
    warnings = run_all_checks(data, config=config)
    graph_paths = []
    with tempfile.TemporaryDirectory() as tmpdir:
        generators = [
            generate_altitude_graph,
            generate_battery_graph,
            generate_speed_graph,
            generate_attitude_graph,
            generate_power_graph,
        ]
        for gen in generators:
            path = gen(data, output_dir=tmpdir)
            if path:
                graph_paths.append(path)
        log_filename = os.path.basename(data["meta"]["filepath"])
        pdf = FlightReport(log_filename)
        pdf.alias_nb_pages()
        pdf.add_title_page()
        pdf.add_summary_section(stats)
        pdf.add_graphs_section(graph_paths)
        pdf.add_warnings_section(warnings)
    filepath = os.path.join(output_dir, "flight_report.pdf")
    pdf.output(filepath)
    print(f"[OK] PDF report saved -> {filepath}")
    return filepath

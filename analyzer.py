import argparse
import sys
import os
from parser import parse_log
from summary import generate_summary, print_summary
from exporter import export_all
from graphs import generate_all_graphs
from anomalies import run_all_checks, print_warnings
from reporter import generate_report
from config import load_config


MENU_OPTIONS = {
    "1": "Flight Summary",
    "2": "Export to CSV",
    "3": "Generate Graphs",
    "4": "Anomaly Warnings",
    "5": "Run All Analysis",
    "6": "Generate PDF Report",
    "7": "Change Log File",
    "8": "Quit",
}



# Legacy fallback constants (overridden by config at runtime)
CSV_OUTPUT_DIR = os.path.join("output", "csv")
GRAPH_OUTPUT_DIR = os.path.join("output", "graphs")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="MAVLink Flight Log Analyzer",
        description=(
            "A command-line tool for parsing and analysing MAVLink .tlog "
            "and ArduPilot .bin flight logs.  Generates summaries, CSV "
            "exports, graphs, and anomaly warnings."
        ),
        epilog=(
            "Examples:\n"
            "  python analyzer.py logs/sample.tlog --summary\n"
            "  python analyzer.py logs/sample.bin  --summary\n"
            "  python analyzer.py logs/sample.tlog --export --graphs\n"
            "  python analyzer.py logs/sample.tlog --all\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "logfile",
        type=str,
        nargs="?",
        default=None,
        help="Path to a .tlog (MAVLink) or .bin (DataFlash) log file to analyse.",
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="Display a flight summary in the terminal.",
    )

    parser.add_argument(
        "--export",
        action="store_true",
        help="Export telemetry data to CSV files in output/csv/.",
    )

    parser.add_argument(
        "--graphs",
        action="store_true",
        help="Generate telemetry graphs as PNG files in output/graphs/.",
    )

    parser.add_argument(
        "--warnings",
        action="store_true",
        help="Run anomaly detection and display warnings.",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all analysis steps (summary + export + graphs + warnings).",
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to a YAML configuration file (default: config.yaml in cwd).",
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive menu mode (no flags needed).",
    )

    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a self-contained PDF report in output/.",
    )

    return parser


def print_banner() -> None:

    print()
    print("==============================================")
    print("|   MAVLink Flight Log Analyzer (CLI)        |")
    print("|   Parse - Summarise - Export - Visualise   |")
    print("|   Supports: .tlog and .bin log formats     |")
    print("==============================================")
    print()


def print_menu() -> None:
    print("\n--- INTERACTIVE MENU ---")
    for key, label in MENU_OPTIONS.items():
        print(f"  [{key}] {label}")
    print()


def get_log_file_interactive() -> str:
    while True:
        path = input("Enter path to log file (.tlog or .bin): ").strip()
        if not path:
            print("[WARN] Path cannot be empty.")
            continue
        if not os.path.isfile(path):
            print(f"[WARN] File not found: {path}")
            continue
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".tlog", ".bin"):
            print(f"[WARN] Unsupported format '{ext}'. Use .tlog or .bin")
            continue
        return path


def load_log_interactive(filepath: str, config: dict) -> dict | None:
    try:
        data = parse_log(filepath, config=config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"\n[ERROR] {exc}")
        return None

    if data["meta"]["parsed_messages"] == 0:
        print("[WARN] No supported messages found in this log.")
        return None

    return data


def run_interactive(filepath: str, config: dict) -> None:
    csv_dir = config["output"]["csv_dir"]
    graph_dir = config["output"]["graph_dir"]

    print_banner()
    data = load_log_interactive(filepath, config)
    if data is None:
        return

    print(f"[INFO] Loaded: {os.path.basename(filepath)}")

    while True:
        print_menu()
        raw = input("Select option(s) (e.g. 1,3 or 2 4): ").strip()

        # Parse: accept "1,3", "1 3", "1, 3, 4", or single "2"
        choices = []
        for part in raw.replace(",", " ").split():
            if part in MENU_OPTIONS:
                choices.append(part)

        if not choices:
            print("[WARN] No valid options selected. Enter numbers 1-8.")
            continue

        # Prevent mixing quit/switch with analysis actions
        if "8" in choices and len(choices) > 1:
            print("[WARN] Quit cannot be combined with other options.")
            continue
        if "7" in choices and any(c in choices for c in "123456"):
            print("[WARN] Change Log File cannot be combined with analysis options.")
            continue

        for choice in choices:
            if choice == "1":
                stats = generate_summary(data)
                print_summary(stats)

            elif choice == "2":
                export_all(data, output_dir=csv_dir)

            elif choice == "3":
                generate_all_graphs(data, output_dir=graph_dir)

            elif choice == "4":
                warning_list = run_all_checks(data, config=config)
                print_warnings(warning_list)

            elif choice == "5":
                stats = generate_summary(data)
                print_summary(stats)
                export_all(data, output_dir=csv_dir)
                generate_all_graphs(data, output_dir=graph_dir)
                warning_list = run_all_checks(data, config=config)
                print_warnings(warning_list)

            elif choice == "6":
                generate_report(data, output_dir="output", config=config)

            elif choice == "7":
                filepath = get_log_file_interactive()
                data = load_log_interactive(filepath, config)
                if data is None:
                    print("[WARN] Could not load new file. Keeping previous data.")
                else:
                    print(f"[INFO] Loaded: {os.path.basename(filepath)}")

            elif choice == "8":
                print("[DONE] Goodbye.\n")
                return


def main() -> None:

    arg_parser = build_arg_parser()
    args = arg_parser.parse_args()

    # Load configuration (from --config path or cwd config.yaml)
    config = load_config(args.config)

    # --- Interactive mode ---
    if args.interactive:
        filepath = args.logfile or get_log_file_interactive()
        run_interactive(filepath, config)
        return

    # --- Flag-based mode ---
    if args.logfile is None:
        arg_parser.print_help()
        print("\n[ERROR] Please provide a log file or use --interactive.")
        sys.exit(1)

    if not any([args.summary, args.export, args.graphs, args.warnings, args.all, args.report]):
        arg_parser.print_help()
        print("\n[ERROR] Please specify at least one action flag "
              "(--summary, --export, --graphs, --warnings, --report, or --all).")
        sys.exit(1)

    if args.all:
        args.summary = True
        args.export = True
        args.graphs = True
        args.warnings = True

    csv_dir = config["output"]["csv_dir"]
    graph_dir = config["output"]["graph_dir"]

    print_banner()

    try:
        data = parse_log(args.logfile, config=config)
    except FileNotFoundError as exc:
        print(f"\n[ERROR] {exc}")
        sys.exit(1)
    except ValueError as exc:
        print(f"\n[ERROR] {exc}")
        sys.exit(1)

    if data["meta"]["parsed_messages"] == 0:
        print("[WARN] No supported messages found in this log.")
        print("       For .tlog: GPS_RAW_INT, GLOBAL_POSITION_INT, "
              "SYS_STATUS, ATTITUDE")
        print("       For .bin : GPS, ATT, BAT")
        sys.exit(0)

    if args.summary:
        stats = generate_summary(data)
        print_summary(stats)

    if args.export:
        export_all(data, output_dir=csv_dir)

    if args.graphs:
        generate_all_graphs(data, output_dir=graph_dir)

    if args.warnings:
        warning_list = run_all_checks(data, config=config)
        print_warnings(warning_list)

    if args.report:
        generate_report(data, output_dir="output", config=config)

    print("[DONE] Analysis complete.\n")


if __name__ == "__main__":
    main()

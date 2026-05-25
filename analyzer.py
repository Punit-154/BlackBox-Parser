
import argparse
import sys
import os
from parser import parse_log
from summary import generate_summary, print_summary
from exporter import export_all
from graphs import generate_all_graphs
from anomalies import run_all_checks, print_warnings



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

    return parser


def print_banner() -> None:
   
    print()
    print("==============================================")
    print("|   MAVLink Flight Log Analyzer (CLI)        |")
    print("|   Parse - Summarise - Export - Visualise   |")
    print("|   Supports: .tlog and .bin log formats     |")
    print("==============================================")
    print()


def main() -> None:
    
    arg_parser = build_arg_parser()
    args = arg_parser.parse_args()

    
    if not any([args.summary, args.export, args.graphs, args.warnings, args.all]):
        arg_parser.print_help()
        print("\n[ERROR] Please specify at least one action flag "
              "(--summary, --export, --graphs, --warnings, or --all).")
        sys.exit(1)

    
    if args.all:
        args.summary = True
        args.export = True
        args.graphs = True
        args.warnings = True

    print_banner()

    
    try:
        data = parse_log(args.logfile)
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
        export_all(data, output_dir=CSV_OUTPUT_DIR)

    if args.graphs:
        generate_all_graphs(data, output_dir=GRAPH_OUTPUT_DIR)

    if args.warnings:
        warning_list = run_all_checks(data)
        print_warnings(warning_list)

    print("[DONE] Analysis complete.\n")


if __name__ == "__main__":
    main()

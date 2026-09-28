"""Command Line and GUI Interface for Hardware Gauntlet."""

import sys
import argparse
from hwscan import __version__, __app_name__
from hwscan.core.system_info import HardwareScannerEngine
from hwscan.reporters.console import ConsoleReporter
from hwscan.reporters.json_reporter import JSONReporter
from hwscan.reporters.markdown import MarkdownReporter
from hwscan.reporters.html_reporter import HTMLReporter


def main():
    parser = argparse.ArgumentParser(
        prog="hwscan",
        description=f"{__app_name__} v{__version__} - Universal Cross-Platform Hardware Scanner & Diagnostic Suite"
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"{__app_name__} v{__version__}"
    )

    parser.add_argument(
        "--gui",
        nargs="?",
        const="auto",
        choices=["auto", "webview", "tk"],
        help="Launch native desktop GUI application window (default when double-clicked)"
    )

    parser.add_argument(
        "--cli",
        action="store_true",
        help="Force terminal console output instead of GUI desktop window"
    )

    parser.add_argument(
        "--full",
        action="store_true",
        help="Run comprehensive scan displaying extended peripherals and subsystem telemetry"
    )

    parser.add_argument(
        "--json",
        nargs="?",
        const="-",
        metavar="FILE",
        help="Export scan results to JSON format (prints to stdout if no file is provided)"
    )

    parser.add_argument(
        "--html",
        nargs="?",
        const="hardware-report.html",
        metavar="FILE",
        help="Generate modern interactive HTML diagnostic report (default: hardware-report.html)"
    )

    parser.add_argument(
        "--markdown",
        nargs="?",
        const="hardware-report.md",
        metavar="FILE",
        help="Export scan results as GitHub Markdown report"
    )

    parser.add_argument(
        "--web",
        action="store_true",
        help="Launch embedded web dashboard & multi-OS download center"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for the embedded web server (default: 8080)"
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host address for the web server (default: 0.0.0.0)"
    )

    parser.add_argument(
        "--health",
        action="store_true",
        help="Check health score only and exit with code 0 (passed) or 1 (critical warnings)"
    )

    args = parser.parse_args()

    # Web Server Mode
    if args.web:
        from hwscan.web.server import start_server
        start_server(host=args.host, port=args.port)
        return

    # Desktop GUI Mode:
    # Triggered if --gui is provided, OR if no arguments are passed and stdin is not a pipe/redirect
    should_launch_gui = bool(args.gui)
    if len(sys.argv) == 1 and not args.cli:
        should_launch_gui = True

    if should_launch_gui and not (args.cli or args.json or args.html or args.markdown or args.health or args.full):
        from hwscan.gui import launch_gui
        engine_choice = args.gui if args.gui in ("auto", "webview", "tk") else "auto"
        launch_gui(prefer_engine=engine_choice)
        return

    # Execute Hardware Scan
    engine = HardwareScannerEngine()
    report = engine.run_full_scan()

    # Health check mode
    if args.health:
        print(f"Hardware Health Score: {report.health_score}/100")
        has_critical = any(w.level == "CRITICAL" for w in report.warnings)
        sys.exit(1 if has_critical or report.health_score < 70 else 0)

    # Output exports
    handled_output = False

    if args.json:
        reporter = JSONReporter()
        if args.json == "-":
            print(reporter.to_json(report))
        else:
            reporter.write_file(report, args.json)
            print(f"[✓] JSON report saved to: {args.json}")
        handled_output = True

    if args.html:
        reporter = HTMLReporter()
        reporter.write_file(report, args.html)
        print(f"[✓] Interactive HTML report generated: {args.html}")
        handled_output = True

    if args.markdown:
        reporter = MarkdownReporter()
        reporter.write_file(report, args.markdown)
        print(f"[✓] Markdown report generated: {args.markdown}")
        handled_output = True

    # Terminal rendering
    if not handled_output or (args.html and not args.json) or (args.markdown and not args.json) or args.cli or args.full:
        reporter = ConsoleReporter()
        reporter.render(report, full=args.full)


if __name__ == "__main__":
    main()

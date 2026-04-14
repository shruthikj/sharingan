"""CLI entry point for Sharingan."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from sharingan import __version__
from sharingan.auth.prod_guard import ProdGuardError, check_prod_guard
from sharingan.config import SharinganConfig
from sharingan.discover.detector import detect_frameworks
from sharingan.generate.test_planner import generate_test_plan
from sharingan.report.generator import generate_report

console = Console()


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize Sharingan in the current project."""
    project_dir = Path(args.dir).resolve()
    commands_dir = project_dir / ".claude" / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)

    src_commands = Path(__file__).parent.parent.parent / "commands"
    if src_commands.exists():
        for cmd_file in src_commands.glob("*.md"):
            dest = commands_dir / cmd_file.name
            dest.write_text(cmd_file.read_text())
            console.print(f"  Installed: /{ cmd_file.stem}", style="green")

    console.print("\nSharingan initialized! Use /sharingan in Claude Code to start.", style="bold green")


def cmd_scan(args: argparse.Namespace) -> None:
    """Scan and discover routes in the target project."""
    project_dir = Path(args.dir).resolve()
    config = SharinganConfig(
        project_dir=project_dir,
        allow_prod=getattr(args, "allow_prod", False),
    )

    try:
        check_prod_guard(config)
    except ProdGuardError as e:
        console.print(f"[bold red]Production guard:[/bold red] {e}")
        sys.exit(1)

    console.print("Scanning project...", style="bold blue")
    frameworks = detect_frameworks(project_dir)

    if not frameworks:
        console.print("No supported frameworks detected.", style="bold red")
        sys.exit(1)

    config.frameworks = [f.name for f in frameworks]

    table = Table(title="Detected Frameworks")
    table.add_column("Framework", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Routes", justify="right", style="magenta")

    for fw in frameworks:
        table.add_row(fw.name, fw.version or "unknown", str(len(fw.routes)))

    console.print(table)

    plan = generate_test_plan(frameworks, config)
    plan_json = plan.model_dump()

    plan_path = config.get_plan_path()
    plan_path.write_text(json.dumps(plan_json, indent=2))
    console.print(f"\nTest plan written to {plan_path}", style="bold green")


def cmd_report(args: argparse.Namespace) -> None:
    """Generate a report from the last test run."""
    project_dir = Path(args.dir).resolve()
    config = SharinganConfig(project_dir=project_dir)
    results_path = config.get_test_output_path() / "results.json"

    if not results_path.exists():
        console.print("No test results found. Run /sharingan-test first.", style="bold red")
        sys.exit(1)

    results = json.loads(results_path.read_text())
    report_md = generate_report(results, config)

    report_path = config.get_report_path()
    report_path.write_text(report_md)
    console.print(f"Report written to {report_path}", style="bold green")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="sharingan",
        description="Autonomous testing agent for Claude Code",
    )
    parser.add_argument("--version", action="version", version=f"sharingan {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    init_parser = subparsers.add_parser("init", help="Initialize Sharingan in your project")
    init_parser.add_argument("--dir", default=".", help="Project directory")

    scan_parser = subparsers.add_parser("scan", help="Scan project and discover routes")
    scan_parser.add_argument("--dir", default=".", help="Project directory")
    scan_parser.add_argument(
        "--allow-prod",
        action="store_true",
        help="Allow scanning when base URL looks like production",
    )

    report_parser = subparsers.add_parser("report", help="Generate report from last run")
    report_parser.add_argument("--dir", default=".", help="Project directory")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args)
    elif args.command == "scan":
        cmd_scan(args)
    elif args.command == "report":
        cmd_report(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

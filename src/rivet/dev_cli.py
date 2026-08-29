from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import ContentAuditor, ReleaseAuditor


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rivet-dev", description="Rivet developer quality gates")
    commands = parser.add_subparsers(dest="command", required=True)
    content = commands.add_parser("audit-content", help="find unfinished or empty release content")
    content.add_argument("path", nargs="?", type=Path, default=Path.cwd())
    content.add_argument("--json", action="store_true")
    release = commands.add_parser("check-release", help="run the strict release audit")
    release.add_argument("path", nargs="?", type=Path, default=Path.cwd())
    release.add_argument("--skip-tests", action="store_true")
    release.add_argument("--skip-build", action="store_true")
    release.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "audit-content":
        report = ContentAuditor(args.path).audit()
        output = json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else report.text("CONTENT AUDIT")
    else:
        report = ReleaseAuditor(args.path).run(not args.skip_tests, not args.skip_build)
        output = json.dumps(report.to_dict(), indent=2, sort_keys=True) if args.json else report.text()
    print(output)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

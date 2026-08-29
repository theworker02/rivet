from __future__ import annotations

import argparse
import compileall
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def run(command: list[str]) -> None:
    print("$", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def check() -> None:
    assert compileall.compile_dir(str(ROOT / "src"), quiet=1)
    assert compileall.compile_dir(str(ROOT / "drivers"), quiet=1)
    run([sys.executable, "-m", "pytest"])
    run([sys.executable, "-m", "rivet", "version"])
    run([sys.executable, "-m", "rivet", "run", "--simulate"])
    run([sys.executable, "-m", "rivet", "verify"])


def audit_content() -> None:
    run([sys.executable, "-m", "rivet.dev_cli", "audit-content", str(ROOT)])


def release_check() -> None:
    run([sys.executable, "-m", "rivet", "check-release"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Rivet developer validation")
    parser.add_argument("command", choices=("check", "audit-content", "release-check"))
    args = parser.parse_args()
    {"check": check, "audit-content": audit_content, "release-check": release_check}[args.command]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

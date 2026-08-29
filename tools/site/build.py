from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "site"
DESTINATION = ROOT / "site-build"


def main() -> None:
    if DESTINATION.exists():
        shutil.rmtree(DESTINATION)
    shutil.copytree(SOURCE, DESTINATION)
    print(f"built documentation site: {DESTINATION}")


if __name__ == "__main__":
    main()

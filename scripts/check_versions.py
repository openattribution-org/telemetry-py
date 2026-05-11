#!/usr/bin/env python3
"""Fail if the SDK version is inconsistent across files (and the JS sibling).

Catches the drift we hit once: pyproject said 0.2.0 while __version__ said 0.1.0,
and telemetry-js had moved on to 0.3.1.

Checks:
  - pyproject.toml `version` == openattribution/telemetry/__init__.py `__version__`
  - if ../telemetry-js/package.json exists, its `version` matches too

Run via `make check-versions` (wired into `make ci`).
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _pyproject_version() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    return data["project"]["version"]


def _dunder_version() -> str:
    text = (ROOT / "src" / "openattribution" / "telemetry" / "__init__.py").read_text()
    m = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    if not m:
        raise SystemExit("could not find __version__ in __init__.py")
    return m.group(1)


def _js_version() -> str | None:
    pkg = ROOT.parent / "telemetry-js" / "package.json"
    if not pkg.exists():
        return None
    return json.loads(pkg.read_text())["version"]


def main() -> int:
    py = _pyproject_version()
    dunder = _dunder_version()
    js = _js_version()

    problems: list[str] = []
    if py != dunder:
        problems.append(f"pyproject.toml ({py}) != __init__.py __version__ ({dunder})")
    if js is not None and js != py:
        problems.append(
            f"telemetry-js package.json ({js}) != telemetry-py ({py}) — bump both together"
        )

    if problems:
        print("version check FAILED:")
        for p in problems:
            print(f"  - {p}")
        return 1

    extra = f", telemetry-js {js}" if js is not None else " (telemetry-js not checked out)"
    print(f"version check OK: {py}{extra}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

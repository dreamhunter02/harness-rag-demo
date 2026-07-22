"""Harness-1 live demo backend.

The upstream project is intentionally pinned as a submodule rather than copied or
patched. Add its repository root to the import path so the demo can reuse its
packages without requiring the upstream flat-layout project to build as a wheel.
"""

import sys
from pathlib import Path


UPSTREAM = Path(__file__).resolve().parents[1] / "vendor" / "harness-1"
if str(UPSTREAM) not in sys.path:
    sys.path.insert(0, str(UPSTREAM))

__version__ = "0.1.0"

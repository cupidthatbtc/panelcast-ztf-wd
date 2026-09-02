#!/usr/bin/env python3
"""Print the v2 runtime code digest (scripts/v2/*.py + frozen_api.py) — used by
the laptop chain's digest gate and by the Mac sync loop."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from v2_common import v2_digest  # noqa: E402

print(v2_digest())

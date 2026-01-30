#!/usr/bin/env python3
"""
CLI entry point for nginx/Traefik converter
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nginx_traefik_converter.main import cli

if __name__ == "__main__":
    cli()

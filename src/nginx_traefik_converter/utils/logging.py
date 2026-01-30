from __future__ import annotations

import logging

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(
    console: Console | None = None,
    level: int = logging.INFO,
) -> None:
    """Set up rich logging configuration."""
    if console is None:
        console = Console()

    # Configure rich logging
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                show_time=False,
                show_path=False,
            ),
        ],
    )

    # Set specific logger levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

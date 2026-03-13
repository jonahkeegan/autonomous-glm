"""
CLI commands for autonomous-glm.

Provides audit, report, propose, and watch commands.
"""

from .audit import audit
from .report import report
from .propose import propose
from .watch import watch
from .dashboard import dashboard

__all__ = [
    "audit",
    "report",
    "propose",
    "watch",
    "dashboard",
]

"""
Agent mock implementations for integration testing.

Provides configurable mock agents that simulate:
- Claude (PM/Arbiter)
- Minimax (Frontend Engineer)
- Codex (Backend Engineer)
- Human (Design Lead)
"""

from tests.integration.mocks.base_mock import BaseAgentMock
from tests.integration.mocks.claude_mock import ClaudeMock
from tests.integration.mocks.minimax_mock import MinimaxMock
from tests.integration.mocks.codex_mock import CodexMock
from tests.integration.mocks.human_mock import HumanMock

__all__ = [
    "BaseAgentMock",
    "ClaudeMock",
    "MinimaxMock",
    "CodexMock",
    "HumanMock",
]
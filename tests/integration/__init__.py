"""
Integration tests for Autonomous-GLM.

Tests multi-module interactions including:
- Agent mocks for protocol testing
- Database integration with real SQLite
- Protocol flow tests (ingest → audit → report → proposal)
- Unix socket transport tests
- Handshake sequence tests
- Arbitration flow tests
"""

import pytest

# Mark all tests in this directory as integration tests
pytestmark = pytest.mark.integration
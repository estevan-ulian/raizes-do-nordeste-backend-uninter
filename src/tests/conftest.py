from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def session():
    session = MagicMock()
    session.add = MagicMock()
    session.exec = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session

import pytest
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def auto_mock_logger():
    """
    Automatically mock the logger for all tests to prevent TypeErrors.

    This fixture patches `logging.getLogger` to return a `MagicMock` with the
    `level` attribute configured. This prevents the `TypeError: '>=' not supported`
    error that occurs when the real logging framework tries to compare a log
    record's level with a mock handler's unconfigured level.
    """
    mock_logger = MagicMock()
    mock_logger.level = logging.INFO
    with patch("logging.getLogger", return_value=mock_logger) as p:
        yield p

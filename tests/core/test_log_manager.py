"""Test the LogManager Class"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from hilsim.core.file_manager import LogManager

# ---------------------------------------------------------------------------------------
# Setup


@pytest.fixture
def log_manager() -> LogManager:
    """Create an instance of the log manager"""
    return LogManager()


# ---------------------------------------------------------------------------------------
# Test instance construction

# No branches


def test_construction() -> None:
    """Test instance construction of the log manager"""
    with patch("hilsim.core.file_manager.logging") as mock_logging:
        log_manager = LogManager()
        mock_logging.Formatter.assert_called_once()
        assert log_manager.root_logger is None
        assert log_manager.handler is None


# ---------------------------------------------------------------------------------------
# Test start_logging() method

# No branches


def test_start_logging_root_logger_setup(log_manager: LogManager) -> None:
    """Test the setup of the root logger in the start_logging() method"""
    root_logger = MagicMock()
    with (
        patch("hilsim.core.file_manager.logging") as mock_logging,
        patch.object(log_manager, "_build_log_filename", return_value="fake_name"),
    ):
        mock_logging.getLogger.return_value = root_logger
        log_manager.start_logging()
        root_logger.setLevel.assert_called_once_with(mock_logging.DEBUG)
        mock_logging.getLogger.assert_called_once()
        assert log_manager.root_logger == root_logger


def test_start_logging_root_handler_setup(log_manager: LogManager) -> None:
    """Test the setup of the handler in the start_logging() method"""
    root_logger = MagicMock()
    handler = MagicMock()
    with (
        patch("hilsim.core.file_manager.logging") as mock_logging,
        patch.object(
            log_manager, "_build_log_filename", return_value="fake_name"
        ) as mock_build_log_name,
    ):
        mock_logging.getLogger.return_value = root_logger
        mock_logging.FileHandler.return_value = handler
        log_manager.start_logging()
        mock_logging.FileHandler.assert_called_once_with("fake_name")
        mock_build_log_name.assert_called_once()
        handler.setLevel.assert_called_once_with(mock_logging.INFO)
        handler.setFormatter.assert_called_once()
        log_manager.root_logger.addHandler.assert_called_once_with(handler)
        assert log_manager.handler == handler


# ---------------------------------------------------------------------------------------
# Test switch_files() method

# No branches


def test_switch_files(log_manager: LogManager) -> None:
    """Test the switch files() method"""
    root_logger = MagicMock()
    old_handler = MagicMock()
    new_handler = MagicMock()

    log_manager.root_logger = root_logger
    log_manager.handler = old_handler

    with (
        patch("hilsim.core.file_manager.logging") as mock_logging,
        patch.object(
            log_manager, "_build_log_filename", return_value="new_fake_name"
        ) as mock_build_file_name,
    ):
        mock_logging.FileHandler.return_value = new_handler
        log_manager.switch_files()
        root_logger.removeHandler.assert_called_once_with(old_handler)
        old_handler.close.assert_called_once()
        mock_logging.FileHandler.assert_called_once_with("new_fake_name")
        new_handler.setLevel.assert_called_once_with(mock_logging.INFO)
        new_handler.setFormatter.assert_called_once_with(log_manager.format)
        log_manager.root_logger.addHandler.assert_called_once_with(new_handler)
        log_manager.handler == new_handler


# ---------------------------------------------------------------------------------------
# Test the _build_log_filename() method


def test_build_log_file_name(log_manager: LogManager) -> None:
    """Test the _build_log_filename() method"""
    with (
        patch("hilsim.core.file_manager.Path.mkdir") as mock_mkdir,
        patch(
            "hilsim.core.file_manager.time.strftime", return_value="time"
        ) as mock_strftime,
    ):
        result = log_manager._build_log_filename()
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_strftime.assert_called_once()
        assert result == (Path.cwd() / "logs") / "log_time.log"


# ---------------------------------------------------------------------------------------

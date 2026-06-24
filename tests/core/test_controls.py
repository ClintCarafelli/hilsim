import pytest

"""Test the Controls module"""

from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from hilsim.core.controls import AdvancedCommunication, Controls

# pylint: disable=redefined-outer-name

# ---------------------------------------------------------------------------------------
# Setup

DEVICE_LIST = ["RP2040_1", "RP2040_2", "STM32_1"]


@pytest.fixture
def controls() -> Controls:
    """construct an instance of the controls object"""
    device_dict = {}

    for device in DEVICE_LIST:
        mock_device = MagicMock()
        mock_device.hb_sm = "ping"
        mock_device.hb_rm = "pong"
        mock_device.advanced_connection.return_value = True
        device_dict[device] = mock_device

    return Controls(cast(dict[str, AdvancedCommunication], device_dict))


# Note: no methods of  the Controls() class branch

# ---------------------------------------------------------------------------------------
# Test heart_beat() method

# Two branches: 
#    - send with advanced connection
#    - send without advanced connection

def test_heart_beat_advanced_connection(controls: Controls) -> None:
    """Test the heart_beat() method with advanced_connection"""
    mock_conn = cast(MagicMock, controls.devices["RP2040_1"].advanced_connection)
    mock_conn.return_value = {"confirmed": True}
    with patch("hilsim.core.controls.logger") as mock_logger:
        result = controls.heart_beat("RP2040_1", True)
        mock_conn.assert_called_once()
        assert result["confirmed"] is True
        mock_logger.info.assert_called_once()

def test_heart_beat_send(controls: Controls) -> None:
    """Test the heart_beat() method without advanced connection"""
    mock_conn = cast(MagicMock, controls.devices["RP2040_1"].send)
    mock_conn.return_value = True
    with patch("hilsim.core.controls.logger") as mock_logger:
        result = controls.heart_beat("RP2040_1")
        mock_conn.assert_called_once()
        assert result["confirmed"] is True
        mock_logger.info.assert_called_once()


# ---------------------------------------------------------------------------------------
# Test advanced_send() method

# No branches

def test_advanced_send(controls: Controls) -> None: 
    """Test the advanced send method"""
    mock_conn = cast(MagicMock, controls.devices["RP2040_1"].advanced_connection)
    mock_conn.return_value = {"confirmed": True}
    result = controls.advanced_send("RP2040_1", "1,1,0")
    assert result.keys() == {"confirmed"}
    assert result["confirmed"] is True

# ---------------------------------------------------------------------------------------
# Test send() method

# No branches

def test_send_controls(controls: Controls) -> None: 
    """Test the send method"""
    mock_send = cast(MagicMock, controls.devices["RP2040_1"].send)
    mock_send.return_value = {"confirmed": True}
    result = controls.send("RP2040_1", "1,1,0")
    assert result.keys() == {"confirmed"}
    assert result["confirmed"] is True

# ---------------------------------------------------------------------------------------




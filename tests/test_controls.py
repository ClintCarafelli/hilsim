"""Test the Controls module"""

from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from src.controls import AdvancedCommunication, Controls

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
    with patch("src.controls.logger") as mock_logger:
        result = controls.heart_beat("RP2040_1", True)
        print(result)
        mock_conn.assert_called_once()
        assert result["confirmed"] is True
        mock_logger.info.assert_called_once()

def test_heart_beat_send(controls: Controls) -> None:
    """Test the heart_beat() method without advanced connection"""
    mock_conn = cast(MagicMock, controls.devices["RP2040_1"].send)
    mock_conn.return_value = True
    with patch("src.controls.logger") as mock_logger:
        result = controls.heart_beat("RP2040_1")
        mock_conn.assert_called_once()
        assert result["confirmed"] is True
        mock_logger.info.assert_called_once()


# ---------------------------------------------------------------------------------------
# Test gpio() method


def test_gpio(controls: Controls) -> None:
    """Test the gpio() method"""
    mock_conn = cast(MagicMock, controls.devices["RP2040_1"].advanced_connection)
    with patch("src.controls.logger"):
        result = controls.gpio("RP2040_1", 8, 1, 10)
        mock_conn.assert_called_once()
        assert result is True


# ---------------------------------------------------------------------------------------
# Test pwm() method


def test_pwm(controls: Controls) -> None:
    """Test the pwm() method"""
    mock_conn = cast(MagicMock, controls.devices["STM32_1"].advanced_connection)
    with patch("src.controls.logger"):
        result = controls.pwm("STM32_1", 4, 15.5, 100000, 15)
        mock_conn.assert_called_once()
        assert result is True


# ---------------------------------------------------------------------------------------
# Test lights_4ch() method


def test_lights_4ch(controls: Controls) -> None:
    """Test the lights_4ch() method"""
    mock_conn = cast(MagicMock, controls.devices["RP2040_2"].advanced_connection)
    with patch("src.controls.logger"):
        result = controls.lights_4ch("RP2040_2", 5, 255, 40, 255, 21)
        mock_conn.assert_called_once()
        assert result is True


# ---------------------------------------------------------------------------------------

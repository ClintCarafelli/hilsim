"""Test the FakeINA260 class"""

from unittest.mock import patch
import pytest
from src.fake_ina260 import FakeINA260


# ---------------------------------------------------------------------------------------
# Setup
@pytest.fixture
def base_config() -> dict:
    "build the base configuration used for testing"
    return {
        "failure_rate": 0,
        "base_states": {
            "power_supply": {"voltage": 12.8, "noise": 0.01},
            "computer": {"current": 1.03, "noise": 0.1},
        },
        "hardware_states": {
            "obj_1": {"on": 1.06, "off": 0, "noise": 0.01},
            "obj_2": {"on": 0.588, "off": 0.1, "noise": 0.2},
        },
    }


@pytest.fixture
def off_status() -> dict:
    "create off status dictonary"
    return {"obj_1": "off", "obj_2": "off"}


@pytest.fixture
def on_status() -> dict:
    """create on status dictonary"""
    return {"obj_1": "on", "obj_2": "on"}


@pytest.fixture
def fake_sensor(base_config: dict) -> FakeINA260:
    """Return instance of FakeINA260 with the base configuration"""
    return FakeINA260(base_config)


# ---------------------------------------------------------------------------------------
# test voltage() property

# Two branches:
#   - successful value generation
#   - failed value generation based on failure rate


def test_voltage_success(fake_sensor: FakeINA260) -> None:
    """Test the successful voltage reading branch"""
    with patch.object(fake_sensor, "_get_same_random", return_value=0.5) as mock_gsr:
        with patch.object(fake_sensor, "_create_noise", return_value=0.5) as mock_cn:
            result = fake_sensor.voltage
            assert result == 13.3
            mock_gsr.assert_called_once_with()
            mock_cn.assert_called_once_with("base", "power_supply")


def test_voltage_failure(fake_sensor: FakeINA260) -> None:
    """Test the failed voltage reading branch"""
    fake_sensor.config["failure_rate"] = 1
    with patch.object(fake_sensor, "_get_same_random", return_value=0.5) as mock_gsr:
        with pytest.raises(Exception):
            fake_sensor.voltage
        mock_gsr.assert_called_once_with()


# ---------------------------------------------------------------------------------------
# test current() property

# Three branches:
#   - successful value generation
#       - if controls are running, return self.current
#       - if controls are not running, call update_current to get updated current
#   - failed value generation based on failure rate


def test_current_success_controls(fake_sensor: FakeINA260) -> None:
    """Test the successful current reading branch with active controls"""
    fake_sensor.controls_running = True
    result = fake_sensor.current
    assert result == 0


def test_current_success_no_controls(fake_sensor: FakeINA260) -> None:
    """Test the successful voltage reading branch with no active controls"""

    def fake_update() -> None:
        """used as a side_effect to mimic the side efffect of 'update_current'"""
        fake_sensor.current_val = 12

    with patch.object(
        fake_sensor, "update_current", side_effect=fake_update
    ) as mock_uc:
        result = fake_sensor.current
        assert result == 12
        mock_uc.assert_called_once_with()


def test_current_failure(fake_sensor: FakeINA260) -> None:
    """test a failed reading of the current property"""
    fake_sensor.config["failure_rate"] = 1
    with patch.object(fake_sensor, "_get_same_random", return_value=0.5) as mock_gsr:
        with pytest.raises(Exception):
            fake_sensor.current
        mock_gsr.assert_called_once_with()


# ---------------------------------------------------------------------------------------
# test power() property

# Two branches:
#   - successful value generation
#   - failed value generation based on failure rate


def test_power_success(fake_sensor: FakeINA260) -> None:
    """test a successful reading of the power property"""
    fake_sensor.current_val = 10
    fake_sensor.voltage_val = 12.8
    result = fake_sensor.power
    assert result == 128


def test_power_failure(fake_sensor: FakeINA260) -> None:
    """test a failed reading of the current property"""
    fake_sensor.config["failure_rate"] = 1
    with patch.object(fake_sensor, "_get_same_random", return_value=0.5) as mock_gsr:
        with pytest.raises(Exception):
            fake_sensor.power
        mock_gsr.assert_called_once_with()


# ---------------------------------------------------------------------------------------
# test update_current() method

# Four branches that rejoin at different stages:
# Deal with hardware status:
#   - if status arg is none, use self.status (saved last status input)
#   - if status arg is not none, update self.status to status, use self.status from
#     there on
# Get current and random factor:
#   - if state of hardware peice is on, get is current value and a noise value
#   - if state of hardware is anything else, current and noise is zero,
#     this reflects the bang-bang nature of the hardware used in the controls and
#     the system in general.


def test_update_current_no_status_input_off(
    fake_sensor: FakeINA260, off_status: dict
) -> None:
    """test current update with no status input and all objects off"""
    fake_sensor.status = off_status
    with patch.object(fake_sensor, "_create_noise", return_value=0.5):
        fake_sensor.update_current()
        assert fake_sensor.current_val == 1.53


def test_update_current_no_status_input_on(
    fake_sensor: FakeINA260, on_status: dict
) -> None:
    """test current update with status input of all objects on"""
    fake_sensor.status = on_status
    with patch.object(fake_sensor, "_create_noise", side_effect=[0.5, 0.5, 0.5]):
        fake_sensor.update_current()
        assert fake_sensor.current_val == 4.178


def test_update_current_status_input(
    fake_sensor: FakeINA260, off_status: dict, on_status: dict
) -> None:
    """test current update with a status input
    (swtich status from all off to all on)"""
    fake_sensor.status = off_status
    with patch.object(fake_sensor, "_create_noise", side_effect=[0.5, 0.5, 0.5]):
        fake_sensor.update_current(on_status)
        assert fake_sensor.current_val == 4.178


# ---------------------------------------------------------------------------------------
# test set_status() method

# No branches, but must make sure it updates self.status to the arg status.


def test_set_status(fake_sensor: FakeINA260, on_status: dict) -> None:
    """test set status method actually sets the status"""
    fake_sensor.set_status(on_status)
    assert fake_sensor.status == on_status


# ---------------------------------------------------------------------------------------
# Test _get_same_random() method

# Returns same random every three calls, two main branches:
#   - if counter % 3 is zero (divisible by three, create new random number and save it)
#   - if counter is not dvisible by three, thna return the saved random number
#   - note the counter should increment after every call to the method


def test_get_same_random(fake_sensor: FakeINA260) -> None:
    """Test the get same random method: make sure it returns same number when
    called three times in a row, and a new number on the 4th"""
    with patch("src.fake_ina260.random", side_effect=[0.1, 0.3]):
        fake_sensor._get_same_random()
        assert fake_sensor.rand_num == 0.1
        assert fake_sensor.counter == 1
        fake_sensor._get_same_random()
        assert fake_sensor.rand_num == 0.1
        assert fake_sensor.counter == 2
        fake_sensor._get_same_random()
        assert fake_sensor.rand_num == 0.1
        assert fake_sensor.counter == 3
        fake_sensor._get_same_random()
        assert fake_sensor.rand_num == 0.3
        assert fake_sensor.counter == 4


# ---------------------------------------------------------------------------------------
# Test _create_noise() method

# Three branches:
#    - category is base, returns noise value
#    - category is hardware, returns noise value
#    - category is neither base nor hardware, returns zero


@pytest.mark.parametrize(
    "category, hw_object",
    [("base", "power_supply"), ("hardware", "obj_1"), ("unknown", "unknown")],
)
def test_create_noise(fake_sensor: FakeINA260, category: str, hw_object: str) -> None:
    """test the base category branch"""
    with patch("src.fake_ina260.random", return_value=1):
        result = fake_sensor._create_noise(category, hw_object)
        if category == "unknown":
            assert result == 0
        else:
            assert result == 0.01


# ---------------------------------------------------------------------------------------

"""Test the ActuatorBase class"""

from unittest.mock import MagicMock, patch

import pytest
from src.actuators import ActuatorBase
from src.controls import Controls
from src.world_state import WorldState

# mypy: disable-error-code=attr-defined

# ---------------------------------------------------------------------------------------
# Setup

CONFIG = {
    "actuator_1": {
        "settings": {
            "name": "actuator_1",
            "driver": "actuator_1_driver",
            "device": "device_1",
            "pin": 8,
            "sim": True,
            "initial_state": "closed",
            "states": ["open", "closed"],
        },
        "failure_sim": {
            "stuck_probability": 0.05,
            "cta_latency": {"distribution": "normal", "mean": 20, "std": 5},
        },
        "effects": {
            "variable_1": {"effect_types": "s+t+p"},
            "variable_2": {"effect_types": "s"},
            "variable_3": {"effect_types": "s+p"},
        },
    }
}


CONTROLLER = MagicMock()
WORLD_STATE = MagicMock()


class ChildClass(ActuatorBase):
    """Test child class, needed to test complete object"""

    def __init__(
        self, config: dict, world_state: WorldState, controller: Controls
    ) -> None:
        super().__init__(config, world_state, controller)

    def build_command(self, target_state):
        """Test build command function"""
        if target_state:
            return "1,1,1"
        return "0,1,1"

    def effect_variable_1(self):
        """Fake effect_ method for testing"""

    def effect_variable_2(self):
        """Fake effect_ method for testing"""

    def effect_variable_3(self):
        """Fake effect_ method for testing"""


@pytest.fixture
def actuator_base():
    """Create an instance of the actuator base that patches the 
    _discover_effects method called in __init__"""
    with patch.object(ActuatorBase, "_discover_effects", return_value="fake_method"):
        yield ActuatorBase(CONFIG["actuator_1"], WORLD_STATE, CONTROLLER)


@pytest.fixture
def child_class() -> ChildClass:
    """Create instance of a child class that inherits from actuator base"""
    return ChildClass(CONFIG["actuator_1"], WORLD_STATE, CONTROLLER)


# ---------------------------------------------------------------------------------------
# Test the __init_subclass__() method


# Make sure multiple subclasses make it to the registry
def test_subclass_registration() -> None:
    """Make sure subclasses are properly registered"""
    ActuatorBase.registry.clear()

    class Plants(ActuatorBase):
        """Child class for registry test"""

    class Solenoid(ActuatorBase):
        """Child class for registry test"""

    assert ActuatorBase.registry == {"Plants": Plants, "Solenoid": Solenoid}


# ---------------------------------------------------------------------------------------
# Test instance construction


# No branches, but uses an instance of ActuatorBase where _discover_effects  is patched,
# and returned with yeild
def test_construction(actuator_base: ActuatorBase) -> None:
    """Test the construction of an instance of ActuatorBase"""
    assert actuator_base._transition_state == "settled"
    assert actuator_base._stuck is False
    assert actuator_base._latency_remaining == 0.0
    assert actuator_base.dt == 0.0
    assert actuator_base.cst == 0.0
    assert actuator_base._stuck_counter == 0
    assert hasattr(actuator_base, "world_state")
    assert hasattr(actuator_base, "failure_sim")
    assert hasattr(actuator_base, "settings")
    assert hasattr(actuator_base, "effects")
    assert hasattr(actuator_base, "sim")
    assert hasattr(actuator_base, "commanded_state")
    assert hasattr(actuator_base, "hardware_state")
    assert hasattr(actuator_base, "name")
    actuator_base._discover_effects.assert_called_once()


# ---------------------------------------------------------------------------------------
# Test send command:

# Branches:
#   - is advanced_connection
#   - is not advanced connection


# Important the the _update_commanded_state method is known to be called with the
# confirmation to eventually update the commanded state field
def test_send_command_advanced_connection(child_class: ChildClass) -> None:
    """Test send command with advanced connection"""
    with (
        patch.object(child_class, "build_command", return_value="0,1,1"),
        patch.object(
            child_class._controller, "advanced_send", return_value={"confirmed": True}
        ),
        patch.object(child_class, "_update_commanded_state"),
    ):
        child_class.send_command("open", True)
        child_class.build_command.assert_called_once_with("open")
        child_class._controller.advanced_send.assert_called_once_with(
            "device_1", "0,1,1"
        )
        child_class._update_commanded_state.assert_called_once_with(
            {"confirmed": True}, "open"
        )


def test_send_command_no_advanced_connection(child_class: ChildClass) -> None:
    """Test send command with send only (no advanced connection)"""
    with (
        patch.object(child_class, "build_command", return_value="0,1,1"),
        patch.object(child_class._controller, "send", return_value={"confirmed": True}),
        patch.object(child_class, "_update_commanded_state"),
    ):
        child_class.send_command("open", False)
        child_class.build_command.assert_called_once_with("open")
        child_class._controller.send.assert_called_once_with("device_1", "0,1,1")
        child_class._update_commanded_state.assert_called_once_with(
            {"confirmed": True}, "open"
        )


# ---------------------------------------------------------------------------------------
# Test _update_commanded_state

# Two branches:
#    - if message was confirmed
#    - if message was not confirmed


def test_update_commanded_state_confirmed(actuator_base: ActuatorBase) -> None:
    """Test updating the commanded state when confirmed"""
    actuator_base._update_commanded_state({"confirmed": True}, "open")
    assert actuator_base.commanded_state == "open"
    assert actuator_base._transition_state == "commanded"


def test_update_commanded_state_not_confirmed(actuator_base: ActuatorBase) -> None:
    """Test updating the commanded state when confirmed"""
    actuator_base._update_commanded_state({"confirmed": False}, "open")
    assert actuator_base.commanded_state == "closed"
    assert actuator_base._transition_state == "settled"


# ---------------------------------------------------------------------------------------
# Test _resolve_state_transition

# Branches:
#   - newly stuck
#   - not stuck
#   - _transition_state is settled
#   - _transition_state is commanded
#   - _transition_state is "pending_latency"
#       - if latency remains (greater than zero)
#       - if latency does not remain (less than or equal to zero)
#           - stuck
#           - not stuck


def test_newly_stuck(actuator_base: ActuatorBase) -> None:
    """Test logging for a newly stuck actuator"""
    actuator_base._stuck = True
    with patch("src.actuators.logger") as mock_logger:
        actuator_base._resolve_state_transition()
        assert actuator_base._stuck_counter == 1
        mock_logger.critical.assert_called_once()


def test_not_stuck(actuator_base: ActuatorBase) -> None:
    """Test returning _stuck_counter to zero after being unstuck"""
    actuator_base._stuck_counter = 12
    actuator_base._stuck = False
    actuator_base._resolve_state_transition()
    assert actuator_base._stuck_counter == 0


def test_transition_state_is_settled(actuator_base: ActuatorBase) -> None:
    """Test a settled transition state (i.e. hardware state equals commanded state)"""
    actuator_base._transition_state = "settled"
    actuator_base._resolve_state_transition()
    assert actuator_base._stuck is False
    assert actuator_base._stuck_counter == 0
    assert actuator_base.commanded_state == "closed"
    assert actuator_base.hardware_state == "closed"


@pytest.mark.parametrize("stuck_result", [(True), (False)])
def test_transition_state_is_commanded(
    actuator_base: ActuatorBase, stuck_result: bool
) -> None:
    """Test commanded logic for resolving the state transition"""
    actuator_base._transition_state = "commanded"
    latency = 20
    with (
        patch.object(actuator_base, "_sample_latency", return_value=latency),
        patch.object(actuator_base, "_sample_stuck", return_value=stuck_result),
    ):
        actuator_base._resolve_state_transition()
        assert actuator_base._transition_state == "pending_latency"
        assert actuator_base._stuck == stuck_result
        assert actuator_base._latency_remaining == 20


def test_pending_latency_greater_than_zero(actuator_base: ActuatorBase) -> None:
    """Test case where pending latency is greater than zero"""
    actuator_base._latency_remaining = 20
    actuator_base._transition_state = "pending_latency"
    actuator_base.dt = 5
    actuator_base._resolve_state_transition()
    assert actuator_base._latency_remaining == 15
    assert actuator_base._transition_state == "pending_latency"
    assert actuator_base.hardware_state == "closed"


def test_pending_latency_equal_to_zero_not_stuck(actuator_base: ActuatorBase) -> None:
    """Test case where pending latency is equal to zero and actuator is not stuck"""
    actuator_base._latency_remaining = 0
    actuator_base._transition_state = "pending_latency"
    actuator_base.dt = 5
    actuator_base._resolve_state_transition()
    assert actuator_base._transition_state == "settled"
    assert actuator_base.hardware_state == "closed"


def test_pending_latency_less_than_zero_not_stuck(actuator_base: ActuatorBase) -> None:
    """Test case where pending latency is less than zero and actuator is not stuck"""
    actuator_base._latency_remaining = -3
    actuator_base._transition_state = "pending_latency"
    actuator_base.dt = 5
    actuator_base._resolve_state_transition()
    assert actuator_base._transition_state == "settled"
    assert actuator_base.hardware_state == "closed"


def test_pending_latency_with_stuck(actuator_base: ActuatorBase) -> None:
    """Test where pending latenct is less than or equal to zero and actuator is stuck"""
    actuator_base._transition_state = "pending_latency"
    actuator_base._latency_remaining = 0
    actuator_base._stuck = True
    actuator_base._resolve_state_transition()
    assert actuator_base._transition_state == "stuck"


# ---------------------------------------------------------------------------------------
# Test _sample_latency() method

# Three branches
#   - distribution type is normal
#   - distribution type is uniform
#   - anything else in the distribution value

# Note, if adding distribution types, tests will need to be added here


@pytest.mark.parametrize(
    "latency",
    [
        (0.002),
        (-0.001),
    ],
)
def test_sample_latency_normal_distribution(
    actuator_base: ActuatorBase, latency: float
) -> None:
    """Test latency derived from a normal distribution, as set in the CONFIG"""
    with patch("src.actuators.gauss", return_value=latency) as mock_gauss:
        result = actuator_base._sample_latency()
        mean_val = actuator_base.failure_sim["cta_latency"]["mean"] / 1000
        std_val = actuator_base.failure_sim["cta_latency"]["std"] / 1000
        mock_gauss.assert_called_once_with(mean_val, std_val)
        if latency < 0:
            assert result == 0
        else:
            assert result == latency


def test_sample_latency_uniform_distribution(actuator_base: ActuatorBase) -> None:
    """Test latency derived from a uniform distribution"""
    actuator_base.failure_sim["cta_latency"]["distribution"] = "uniform"
    actuator_base.failure_sim["cta_latency"]["min"] = 5
    actuator_base.failure_sim["cta_latency"]["max"] = 50
    with patch("src.actuators.uniform", return_value=0.0025) as mock_uniform:
        result = actuator_base._sample_latency()
        min_val = actuator_base.failure_sim["cta_latency"]["min"] / 1000
        max_val = actuator_base.failure_sim["cta_latency"]["max"] / 1000
        assert result == 0.0025
        mock_uniform.assert_called_once_with(min_val, max_val)


def test_sample_latency_unknown_distribution(actuator_base: ActuatorBase) -> None:
    """Test latency derived from an unknown / not implimented distributiion type 
    (i.e. return latency as zero)"""
    actuator_base.failure_sim["cta_latency"]["distribution"] = "not_a_distirbution"
    with patch("src.actuators.logger") as mock_logger:
        result = actuator_base._sample_latency()
        mock_logger.warning.assert_called_once()
        assert result == 0


# ---------------------------------------------------------------------------------------
# Test _sample_stuck() method

# Two branches:
#   - stuck (return True)
#   - not stuck (return False)


@pytest.mark.parametrize("random_return_val, return_val", [(0, True), (1, False)])
def test_sample_stuck(
    actuator_base: ActuatorBase, random_return_val: float, return_val: bool
) -> None:
    """test _sample_stuck"""
    with patch("src.actuators.random", return_value=random_return_val):
        result = actuator_base._sample_stuck()
        assert result == return_val


# ---------------------------------------------------------------------------------------
# Test _update() method

# No branches, just make sure _resolve_state_transition() and _apply_effects()
# are called, and that cst and dt attributes are called


def test_update(actuator_base: ActuatorBase) -> None:
    """Test the update method"""
    actuator_base.cst = 25
    with (
        patch.object(actuator_base, "_resolve_state_transition") as mock_rst,
        patch.object(actuator_base, "_apply_effects") as mock_ae,
    ):
        actuator_base.update(5)
        assert actuator_base.dt == 5
        assert actuator_base.cst == 30
        mock_rst.assert_called_once()
        mock_ae.assert_called_once()


# ---------------------------------------------------------------------------------------
# Test _discover_effects() method

# No branches. This method finds any methods that are prefixed with effect in the
# compiled object. None exist in the parent class, so all derive from the child class

# Also note that inspect.getmembers returns a list of (name, value) tuples


def test_discover_effects(child_class: ChildClass) -> None:
    """Test the _discover_effects() method"""
    child_class._discover_effects()
    em_dict = child_class._effect_methods
    assert len(em_dict) == 3
    should_be_keys = {"variable_1", "variable_2", "variable_3"}
    assert should_be_keys <= em_dict.keys()
    assert em_dict["variable_1"] == child_class.effect_variable_1
    assert em_dict["variable_2"] == child_class.effect_variable_2
    assert em_dict["variable_3"] == child_class.effect_variable_3


# ---------------------------------------------------------------------------------------
# Test _apply_effects() method

# Two branches:
#   - if "p" is in memory type (effect to variable lingers after actuator changes state)
#   - if "p" is not in memory type (effects don't linger after state change)

# Both branches will reflect in the call counts to methods of the world_state attribute


def test_apply_effects(child_class: ChildClass) -> None:
    """Test the apply_effects() method"""
    child_class._apply_effects()
    assert child_class.world_state.apply_delta.call_count == 2
    assert child_class.world_state.add_contributions.call_count == 1


# ---------------------------------------------------------------------------------------
# Test _get_memory_type_method() method

# No branches:


def test_get_memory_type(actuator_base: ActuatorBase) -> None:
    """Test the get_memory_type() method"""
    result = actuator_base._get_memory_type("variable_1")
    assert result == "s+t+p"


# ---------------------------------------------------------------------------------------

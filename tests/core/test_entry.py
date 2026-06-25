import pytest
from pathlib import Path
from rich.table import Table
from unittest.mock import patch, MagicMock
from hilsim.core.entry import build_context
from hilsim.core.entry import build_hardware
from hilsim.core.entry import build_sensor_stack
from hilsim.core.entry import build_table
from hilsim.core.entry import background_dynamics
from hilsim.core.entry import run

# ---------------------------------------------------------------------------------------
# Setup


@pytest.fixture
def build_ctx(sensor_config: dict, device_config: dict, actuator_config: dict) -> None:
    """Create build_ctx for testing"""
    return {
        "sensor_config": sensor_config,
        "device_config": device_config,
        "actuator_config": actuator_config,
        "world_state": MagicMock(),
        "i2c_bus": MagicMock(),
        "project_root": Path("root"),
    }


@pytest.fixture
def hardware() -> None:
    """Create hardware that would be created in build_hardware"""
    return {
        "sensors": {"sensor_1": MagicMock(), "sensor_2": MagicMock()},
        "actuators": {"actuator_1": MagicMock(), "actuator_2": MagicMock()},
    }


# ---------------------------------------------------------------------------------------
# Test the build_context() function

# No branches


def test_build_context(
    sensor_config: dict,
    device_config: dict,
    actuator_config: dict,
    world_state_config: dict,
) -> None:
    """Test the build_context method"""
    with (
        patch(
            "hilsim.core.entry.LoadTOML",
            side_effect=[
                world_state_config,
                device_config,
                actuator_config,
                sensor_config,
            ],
        ),
        patch("hilsim.core.entry.WorldState"),
        patch("hilsim.core.entry.I2CBus"),
    ):

        result = build_context(Path("root"))
    assert result.keys() == {
        "sensor_config",
        "device_config",
        "actuator_config",
        "world_state",
        "i2c_bus",
        "project_root",
    }
    assert result["sensor_config"] == sensor_config
    assert result["device_config"] == device_config
    assert result["actuator_config"] == actuator_config
    assert isinstance(result["world_state"], MagicMock)
    assert isinstance(result["i2c_bus"], MagicMock)
    assert result["project_root"] == Path("root")


# ---------------------------------------------------------------------------------------
# Test the build_hardware() function

# No branches


def test_build_hardware(build_ctx: dict, hardware: dict) -> None:
    """Test teh build_hardware() function"""
    with patch("hilsim.core.entry.BuildComponents") as mock_build_Components:
        mock_build_Components.return_value.build_all.return_value = hardware
        sensors, actuators = build_hardware(build_ctx)
        assert sensors.keys() == {"sensor_1", "sensor_2"}
        assert actuators.keys() == {"actuator_1", "actuator_2"}


# ---------------------------------------------------------------------------------------
# Test the build_sensor_stack() function

# No Branches


def test_build_sensor_stack(build_ctx: dict) -> None:
    """Test teh build_hardware() function"""
    with (
        patch("hilsim.core.entry.SensorManager") as mock_sensor_manager,
        patch("hilsim.core.entry.SensorTracker"),
    ):
        sm, st = build_sensor_stack(
            build_ctx["sensor_config"], MagicMock(), MagicMock()
        )
        sm.initialize_all.assert_called_once()
        assert isinstance(sm, MagicMock)
        assert isinstance(st, MagicMock)


# ---------------------------------------------------------------------------------------
# Test the build_table() function

# No Branches


def test_build_table() -> None:
    """Test the build_table() function"""
    sensor_manager = MagicMock()
    sensor_manager.read_all.return_value=("test_data", "time")
    top_header_val = ["sensor_1", "sensor_1", "system_clock"]
    bottom_header_val = ["temp", "pressure", "time (UNIX)"]
    sensor_manager.build_header.return_value = [top_header_val, bottom_header_val]
    table, top_header, bottom_header = build_table(sensor_manager)
    sensor_manager.read_all.assert_called_once()
    sensor_manager.build_header.assert_called_once()
    assert top_header == ["sensor_1", "sensor_1", "system_clock"]
    assert bottom_header == ["temp", "pressure", "time (UNIX)"]
    assert isinstance(table, Table)


# ---------------------------------------------------------------------------------------
# Test the background_dynamics() function

# Two branches:
#    - sucess
#    - raises an exception
#    - Note: this is caught by the Stopper class as a side effect of sleep. As the thread
#      were to run, it eventually raises a StopIteration exception, which is then
#      caught in the function, allowing it to exit cleanly. So both paths are actually
#      getting tested in this one function.


def test_background_dynamics_success() -> None:
    """Test successffully running the background dynamics"""
    world_state = MagicMock()
    actuator_1_obj = MagicMock()
    actuator_2_obj = MagicMock()
    actuators = {"actuator_1": actuator_1_obj, "actuator_2": actuator_2_obj}

    class Stopper:
        def __init__(self) -> None:
            self.call_count = 0

        def force_stop(self, duration):
            """Force a stop after three calls by raising an exception"""
            self.call_count += 1
            if self.call_count >= 3:
                raise StopIteration("done")

    stopper_instance = Stopper()

    with (
        patch(
            "hilsim.core.entry.time.sleep", side_effect=stopper_instance.force_stop(0)
        ),
        patch("hilsim.core.entry.time.time", side_effect=[0.0, 0.0, 0.01, 0.02, 0.03]),
    ):
        background_dynamics(world_state, actuators)

    assert actuator_1_obj.update.call_count == 4
    assert actuator_2_obj.update.call_count == 4
    assert world_state.update_state.call_count == 4


# ---------------------------------------------------------------------------------------
# Test the run() function

# No branches


def test_run() -> None:
    """Test the run function"""
    with (
        patch("hilsim.core.entry.LogManager") as mock_log_manager,
        patch("hilsim.core.entry.build_context") as mock_build_context,
        patch(
            "hilsim.core.entry.build_hardware", return_value=(MagicMock(), MagicMock())
        ) as mock_build_hardware,
        patch(
            "hilsim.core.entry.build_sensor_stack",
            return_value=(MagicMock(), MagicMock()),
        ) as mock_build_sensor_stack,
        patch(
            "hilsim.core.entry.build_table",
            return_value=(MagicMock(), MagicMock(), MagicMock()),
        ) as mock_build_table,
        patch("hilsim.core.entry.DataManager") as mock_data_manager,
        patch("hilsim.core.entry.threading.Thread") as mock_threading,
        patch("hilsim.core.entry.import_user_main") as mock_importer,
    ):
        run(Path("root"))
        mock_log_manager.assert_called_once()
        mock_log_manager.return_value.start_logging.assert_called_once()
        mock_build_context.assert_called_once()
        mock_build_hardware.assert_called_once()
        mock_build_sensor_stack.assert_called_once()
        mock_build_table.assert_called_once()
        mock_data_manager.assert_called_once()
        mock_threading.assert_called_once()
        _, kwargs = mock_threading.call_args
        assert kwargs["daemon"] is True
        mock_threading.return_value.start.assert_called_once()
        mock_importer.assert_called_once_with(Path("root"))
        mock_importer.return_value.main.assert_called_once()


# ---------------------------------------------------------------------------------------

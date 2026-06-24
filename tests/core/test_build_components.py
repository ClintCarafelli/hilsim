"""Test the BuildComponents class"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from hilsim.core.actuators import ActuatorBase
from hilsim.core.builders import BuildComponents
from hilsim.core.controls import DeviceConnectionError
from hilsim.core.sensors import DriverBase, SensorBase

# ---------------------------------------------------------------------------------------
# Setup

I2C_BUS = MagicMock()
PROJECT_ROOT = Path("fake_project")
CONTROLLER = MagicMock()


@pytest.fixture
def ctx(
    sensor_config: dict,
    actuator_config: dict,
    device_config: dict,
    world_state_config: dict,
) -> dict:
    """Create the context dictonary passed into the builder class"""
    return {
        "sensor_config": sensor_config,
        "actuator_config": actuator_config,
        "device_config": device_config,
        "world_state": world_state_config,
        "i2c_bus": I2C_BUS,
        "project_root": PROJECT_ROOT,
    }


@pytest.fixture
def build_actuator_base_registry(ctx: dict) -> dict:
    """Mock the classes in the actuator base registry"""
    actuator_base_registry = {}
    for config in ctx["actuator_config"].values():
        driver_name = config["settings"]["driver"]
        actuator_base_registry[driver_name] = MagicMock()
    return actuator_base_registry


@pytest.fixture
def build_sensor_base_registry(ctx: dict) -> dict:
    """Mock the classes in the actuator base registry"""
    sensor_base_registry = {}
    for config in ctx["sensor_config"]["sensors"].values():
        fake_sensor_name = config["fake_sensor_name"]
        sensor_base_registry[fake_sensor_name] = MagicMock()
    return sensor_base_registry


@pytest.fixture
def build_driver_base_registry(ctx: dict) -> dict:
    """Mock the classes in the actuator base registry"""
    driver_base_registry = {}
    mock_class = MagicMock()
    mock_class.__name__ = "fake_class"
    for config in ctx["sensor_config"]["sensors"].values():
        driver_name = config["driver_name"]
        driver_base_registry[driver_name] = mock_class
    return driver_base_registry


@pytest.fixture
def yield_builder(ctx: dict):
    """Construct an instance of the BuildComponents class,
    yielding with _auto_discover patched"""
    with patch.object(BuildComponents, "_auto_discover"):
        yield BuildComponents(ctx)


@pytest.fixture
def builder(ctx: dict) -> BuildComponents:
    """Construct an instance of the BuildComponents class"""
    return BuildComponents(ctx)


# ---------------------------------------------------------------------------------------
# Test instance construction:

# No branches


def test_instance_construction_attributes(
    ctx: dict, yield_builder: BuildComponents
) -> None:
    """Test that the instance is constructed correctly"""
    assert yield_builder.sensor_config == ctx["sensor_config"]
    assert yield_builder.device_config == ctx["device_config"]
    assert yield_builder.actuator_config == ctx["actuator_config"]
    assert yield_builder.world_state == ctx["world_state"]
    assert yield_builder.i2c_bus == ctx["i2c_bus"]
    assert yield_builder.project_root == ctx["project_root"]


def test_instance_construction_auto_discover(ctx: dict) -> None:
    """Test that two calls are made to the _auto_discover method"""
    with patch.object(BuildComponents, "_auto_discover") as mock_ad:
        BuildComponents(ctx)
        assert mock_ad.call_count == 2
        mock_ad.assert_any_call(ctx["project_root"] / "sensors")
        mock_ad.assert_any_call(ctx["project_root"] / "actuators")


def test_instance_construction_raises_on_missing_key(ctx: dict) -> None:
    """Test raising a keyerror if ctx is missing needed key"""
    with pytest.raises(KeyError):
        BuildComponents({})


# ---------------------------------------------------------------------------------------
# Test _auto_discover() method

# Branches:
#  - successful import
#  - skip file names that start with "_"
#  - catch Import Errors and raise them


def test_auto_discover_successful_import(
    builder: BuildComponents, tmp_path: Path
) -> None:
    """Test successfully importing a module"""
    module_file = tmp_path / "my_module.py"
    module_file.write_text("x=1")
    builder._auto_discover(tmp_path)


def test_auto_discover_skips_dunder_files(
    builder: BuildComponents, tmp_path: Path
) -> None:
    """Test that auto_discover skips dunder files like __init__.py"""
    dunder_file = tmp_path / "__init__.py"
    dunder_file.write_text("This should not be imported")
    with patch("importlib.util.spec_from_file_location") as mock_spec:
        builder._auto_discover(tmp_path)
        mock_spec.assert_not_called()


def test_auto_discover_raises_on_bad_module(
    builder: BuildComponents, tmp_path: Path
) -> None:
    """Test catching and raising on failed imports"""
    bad_module = tmp_path / "bad_module.py"
    bad_module.write_text("!!!@@@")

    with pytest.raises(ImportError, match="failed to load module"):
        builder._auto_discover(tmp_path)


# ---------------------------------------------------------------------------------------
# Test _build_actuators() method

# No branches


def test_build_actuators(
    ctx: dict, builder: BuildComponents, build_actuator_base_registry: dict
) -> None:
    """Test the build actuators function"""
    builder.controller = CONTROLLER
    ActuatorBase.registry = build_actuator_base_registry
    results = builder._build_actuators()
    correct_keys = ctx["actuator_config"].keys()
    assert results.keys() == correct_keys
    for val in results.values():
        assert isinstance(val, MagicMock)


# ---------------------------------------------------------------------------------------
# Test _build_fake_sensors_with_drivers() method

# No branches


def test_build_fake_sensors_with_drivers(
    ctx: dict,
    builder: BuildComponents,
    build_sensor_base_registry: dict,
    build_driver_base_registry: dict,
) -> None:
    """Test the _build_fake_sensors_with_drivers method"""
    SensorBase.registry = build_sensor_base_registry
    DriverBase.registry = build_driver_base_registry
    results = builder._build_fake_sensors_with_drivers()
    assert results.keys() == ctx["sensor_config"]["sensors"].keys()
    for val in results.values():
        assert isinstance(val, MagicMock)


# ---------------------------------------------------------------------------------------
# Test _build_devices() method

# Branches:
#  - Successfully create and connect to device
#  - Fail to connect to a device


def test_build_devices_success(ctx: dict, builder: BuildComponents) -> None:
    """Test successfully building devices"""
    with (
        patch("hilsim.core.builders.SerialInterface"),
        patch("hilsim.core.builders.AdvancedCommunication"),
        patch("hilsim.core.builders.logger"),
    ):
        results = builder._build_devices()
        assert results.keys() == ctx["device_config"]["devices"].keys()
        for val in results.values():
            assert isinstance(val, MagicMock)


def test_build_devices_failure(builder: BuildComponents) -> None:
    """Test successfully building devices"""
    with (
        patch("hilsim.core.builders.SerialInterface"),
        patch("hilsim.core.builders.AdvancedCommunication") as mock_ac,
        patch("hilsim.core.builders.logger"),
    ):
        mock_instance = mock_ac.return_value
        mock_instance.device.connect.return_value = False
        with pytest.raises(DeviceConnectionError):
            builder._build_devices()


# ---------------------------------------------------------------------------------------
# Test _build_all() method

# No Branches:


def test_build_all(
    ctx: dict,
    builder: BuildComponents,
    build_actuator_base_registry: dict,
    build_sensor_base_registry: dict,
    build_driver_base_registry: dict,
) -> None:
    """Test the build_all() method"""
    ActuatorBase.registry = build_actuator_base_registry
    SensorBase.registry = build_sensor_base_registry
    DriverBase.registry = build_driver_base_registry
    with patch("hilsim.core.builders.Controls"):
        results = builder.build_all()
        assert results.keys() == {"sensors", "actuators"}
        sensor_results = results["sensors"]
        actuator_results = results["actuators"]
        assert sensor_results.keys() == ctx["sensor_config"]["sensors"].keys()
        assert actuator_results.keys() == ctx["actuator_config"].keys()


# ---------------------------------------------------------------------------------------

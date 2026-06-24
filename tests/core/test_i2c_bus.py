
import pytest
from unittest.mock import patch, MagicMock
from hilsim.core.i2c_bus import I2CBus
from hilsim.core.i2c_exceptions import I2CInitError, I2CDeInitError

# ---------------------------------------------------------------------------------------
# Setup
@pytest.fixture
def sim_i2c_bus() -> I2CBus:
    """Create i2c bus for full-sim mode case"""
    return I2CBus(True)

@pytest.fixture
def real_i2c_bus() -> I2CBus:
    """Create i2c bus for real case """
    return I2CBus(False)


# ---------------------------------------------------------------------------------------
# Test construction
def test_instance_construction(real_i2c_bus: I2CBus) -> None: 
    """Test the instance construction of an i2c bus object"""
    assert real_i2c_bus.initialized is False
    assert hasattr(real_i2c_bus, "sim_all")

# ---------------------------------------------------------------------------------------
# Test the initialize_i2c_bus() method

# Three branches: 
#   - sim all
#   - successfully set up real i2c bus
#   - exception raised when setting up real i2c bus 

def test_sim_initialization(sim_i2c_bus: I2CBus) -> None:
    """Test a sim all initialization"""
    assert sim_i2c_bus.initialized is False
    result = sim_i2c_bus.initialize_i2c_bus()
    assert sim_i2c_bus.initialized is True
    assert result is None

def test_initialization_success(real_i2c_bus: I2CBus) -> None:
    """Test successfully initializing a real i2c bus"""
    mock_board = MagicMock()
    mock_busio = MagicMock()
    assert real_i2c_bus.initialized is False
    with patch.dict("sys.modules", {"board": mock_board, "busio": mock_busio}):
        result = real_i2c_bus.initialize_i2c_bus()
        mock_busio.I2C.assert_called_once_with(mock_board.SCL, mock_board.SDA)
        assert result is mock_busio.I2C.return_value
        assert real_i2c_bus.initialized is True

def test_initialization_fail(real_i2c_bus: I2CBus) -> None:
    """Test a failed initilazation of the i2c bus"""
    mock_busio = MagicMock()
    mock_board = MagicMock()
    assert real_i2c_bus.initialized is False
    with patch.dict("sys.modules", {"board": mock_board, "busio": mock_busio}):
        mock_busio.I2C.side_effect=Exception("fail")
        with pytest.raises(I2CInitError):
            real_i2c_bus.initialize_i2c_bus()
        assert real_i2c_bus.initialized is False

# ---------------------------------------------------------------------------------------
# Test the deinitialize_i2c_bus() method

# Four branches: 
#   - not intialized
#   - sim_all true
#   - successful dinit
#   - failed dinit

def test_deinitialization_catch(real_i2c_bus: I2CBus) -> None:
    """not the not deinitialization, 'not initialized' catch"""
    i2c_bus = None
    with pytest.raises(I2CDeInitError):
        real_i2c_bus.deinitialize_i2c_bus(i2c_bus)

def test_deinitialization_success(real_i2c_bus: I2CBus) -> None:
    """Test successfully deinitializing the i2c bus"""
    real_i2c_bus.initialized = True
    i2c_bus = MagicMock()
    real_i2c_bus.deinitialize_i2c_bus(i2c_bus)
    assert real_i2c_bus.initialized is False 

def test_deinitialization_fail(real_i2c_bus: I2CBus) -> None:
    """Test failing to deinitialize the i2c bus"""
    i2c_bus = MagicMock()
    real_i2c_bus.initialized = True
    i2c_bus.dinit.side_effect = Exception("fail")
    with (patch("hilsim.core.i2c_bus.logger"),
         pytest.raises(I2CDeInitError)):
        real_i2c_bus.deinitialize_i2c_bus(i2c_bus)

def test_deinitialization_sim_all(real_i2c_bus: I2CBus) -> None:
    """Test failing to deinitialize the i2c bus"""
    i2c_bus = MagicMock()
    real_i2c_bus.initialized = True
    real_i2c_bus.sim_all = True
    with patch("hilsim.core.i2c_bus.logger"):
        real_i2c_bus.deinitialize_i2c_bus(i2c_bus)

# ---------------------------------------------------------------------------------------
    

    
        

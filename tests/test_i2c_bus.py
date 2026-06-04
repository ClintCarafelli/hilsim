import pytest
from unittest.mock import patch, MagicMock
from src.i2c_bus import I2CBus
from src.i2c_exceptions import I2CInitError, I2CDeInitError

@pytest.fixture
def sim_i2c_bus():
    return I2CBus(True)

@pytest.fixture
def real_i2c_bus():
    return I2CBus(False)

def test_sim_initialization(sim_i2c_bus):
    assert sim_i2c_bus.initialized is False
    result = sim_i2c_bus.initialize_i2c_bus()
    assert sim_i2c_bus.initialized is True
    assert result is None

def test_initialization_success(real_i2c_bus):
    mock_board = MagicMock()
    mock_busio = MagicMock()
    assert real_i2c_bus.initialized is False
    with patch.dict("sys.modules", {"board": mock_board, "busio": mock_busio}):
        result = real_i2c_bus.initialize_i2c_bus()
        mock_busio.I2C.assert_called_once_with(mock_board.SCL, mock_board.SDA)
        assert result is mock_busio.I2C.return_value
        assert real_i2c_bus.initialized is True

def test_initialization_fail(real_i2c_bus):
    mock_busio = MagicMock()
    mock_board = MagicMock()
    assert real_i2c_bus.initialized is False
    with patch.dict("sys.modules", {"board": mock_board, "busio": mock_busio}):
        mock_busio.I2C.side_effect=Exception("fail")
        with pytest.raises(I2CInitError):
            real_i2c_bus.initialize_i2c_bus()
        assert real_i2c_bus.initialized is False

def test_deinitialization_catch(real_i2c_bus):
    i2c_bus = None
    with pytest.raises(I2CDeInitError):
        real_i2c_bus.deinitialize_i2c_bus(i2c_bus)

def test_deinitialization_success(real_i2c_bus):
    real_i2c_bus.initialized = True
    i2c_bus = MagicMock()
    real_i2c_bus.deinitialize_i2c_bus(i2c_bus)
    assert real_i2c_bus.initialized is False 

def test_deinitialization_fail(real_i2c_bus):
    i2c_bus = MagicMock()
    with pytest.raises(I2CDeInitError):
        real_i2c_bus.deinitialize_i2c_bus(i2c_bus)

    

    
        





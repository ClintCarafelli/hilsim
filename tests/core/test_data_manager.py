import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from collections.abc import Iterable

from hilsim.core.file_manager import DataManager
from hilsim.core.sensors import Reading

# ---------------------------------------------------------------------------------------
# Setup

@ pytest.fixture
def output_dir() -> Path: 
    """Create path for testing"""
    return Path("/tmp")

@pytest.fixture
def headers() -> list[Iterable]: 
    return [["sensor_1", "sensor_1"],["var_1", "var_2"]]

@pytest.fixture
def data_manager(output_dir: Path, headers: list[Iterable]) -> DataManager: 
    """Construct instance of data manager for testing"""
    return DataManager(output_dir, headers)

# ---------------------------------------------------------------------------------------
# Test construction

# No branches, but really important to make sure atexit.register is getting 
# called with the close function here to ensure cleanup

def test_construction_with_file_name(output_dir: Path, headers: list[Iterable]) -> None: 
    """Test instance construction with a data filename input"""
    fake_file_name = "fake_file_name"
    with (patch("hilsim.core.file_manager.Path.mkdir") as mock_mkdir,
          patch("hilsim.core.file_manager.atexit.register") as mock_atexit_register,
          patch.object(DataManager, "_open_file") as mock_open_file,
          patch.object(DataManager, "_resolve_file_name", return_value=fake_file_name)): 
        data_manager = DataManager(output_dir, headers, fake_file_name)
        assert data_manager.headers == headers
        assert data_manager.data_dir == output_dir
        assert data_manager.counter == 0 
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_open_file.assert_called_once()
        mock_atexit_register.assert_called_once_with(data_manager.close)


# ---------------------------------------------------------------------------------------
# Test swap_data_file() method

# No branches 

def test_swap_data_file(data_manager: DataManager) -> None: 
    """Test the swap_data_file_method()"""
    with (patch.object(data_manager, "_resolve_file_name", return_value="new_file_name") as mock_resolve_file_name, 
          patch.object(data_manager, "close") as mock_close,
          patch.object(data_manager, "_open_file") as mock_open_file):
        data_manager.swap_data_file()
        mock_resolve_file_name.assert_called_once()
        mock_close.assert_called_once()
        mock_open_file.assert_called_once_with("new_file_name")
        assert data_manager.counter == 0 


# ---------------------------------------------------------------------------------------
# Test resolve_file_name() method

# Two Branches: 
#   - filename input is None
#   - filename input is a string

def test_resolve_file_name_with_none_input(data_manager: DataManager) -> None:
    """Test the _resolve_file_name() method with None input"""
    with patch("hilsim.core.file_manager.time.strftime", return_value="time") as mock_strftime:
        result = data_manager._resolve_file_name(None)
        mock_strftime.assert_called_once()
        assert result == "time.csv"


def test_resolve_file_name_with_string_input(data_manager: DataManager) -> None:
    """Test the _resolve_file_name() method with string input"""
    with patch("hilsim.core.file_manager.time.strftime", return_value="time") as mock_strftime:
        result = data_manager._resolve_file_name("file_name")
        mock_strftime.assert_not_called()
        assert result == "file_name.csv"

# ---------------------------------------------------------------------------------------
# Test open_file() method

# No branches

def test_open_file(data_manager: DataManager) -> None: 
    """Test the resolve_file_name method()"""
    file = MagicMock()
    writer = MagicMock()
    with (patch("builtins.open", return_value=file) as mock_open,
          patch("hilsim.core.file_manager.csv.writer", return_value=writer) as mock_writer): 
        data_manager._open_file("file_name.csv")
        mock_open.assert_called_once()
        _, kwargs  = mock_open.call_args
        assert kwargs["mode"] == "w"
        assert kwargs["newline"] == ""
        assert kwargs["encoding"] == "utf-8"
        mock_writer.assert_called_once_with(file)
        assert writer.writerow.call_count == 2 
        file.flush.assert_called_once()


# ---------------------------------------------------------------------------------------
# Test add_data_to_file() method

# Three branches: 
#    - n is not None and , n <=0
#    - n is not None
#    - n is None
#    - n is how many calls to add_data_file are made before flushing

@pytest.fixture
def fake_sensing_data() -> dict: 
    """Create fake data for testing"""
    return {"sensor_1": {"var_1": Reading(1, "units_1"), 
                         "var_2":  Reading(2, "units_2")}, 
             "sensor_2": {"var_3":  Reading(3, "units_3")}}

def test_open_file_n_is_not_none_and_leq_zero(data_manager: DataManager, fake_sensing_data: dict) -> None: 
    """Test the case of open_file where n is not None and leq 0"""
    with pytest.raises(ValueError):
        data_manager.add_data_to_file(fake_sensing_data, 0, -1)
    with pytest.raises(ValueError):
         data_manager.add_data_to_file(fake_sensing_data, 0, 0)

def test_open_file_n_is_none(data_manager: DataManager, fake_sensing_data: dict) -> None: 
    """Test the case of open_file where n is None"""
    writer = MagicMock()
    file = MagicMock()

    data_manager.writer = writer
    data_manager.file = file
    data_manager.add_data_to_file(fake_sensing_data, 0)
    data_manager.writer.writerow.assert_called_once()
    data_manager.file.flush.assert_called_once()
    assert data_manager.counter == 0 


def test_open_file_n_is_positive_int(data_manager: DataManager, fake_sensing_data: dict) -> None: 
    """Test the case of open_file where n is greater than 0"""
    writer = MagicMock()
    file = MagicMock()
    data_manager.writer = writer
    data_manager.file = file
    data_manager.add_data_to_file(fake_sensing_data, 0, 2)
    data_manager.writer.writerow.assert_called_once()
    data_manager.file.flush.assert_not_called()
    assert data_manager.counter == 1 
    data_manager.add_data_to_file(fake_sensing_data, 0, 2)
    assert data_manager.writer.writerow.call_count == 2
    data_manager.file.flush.assert_called_once()
    assert data_manager.counter == 2

# ---------------------------------------------------------------------------------------
# Test close() method

# Two branches: 
#   - file aleady closed
#   - file not closed

def test_close_already_closed(data_manager: DataManager) -> None: 
    """Test the close method when the file is already closed"""
    file = MagicMock()
    writer = MagicMock()
    data_manager.file = file
    data_manager.writer = writer
    data_manager.file.closed = True
    data_manager.close()
    data_manager.file.flush.assert_not_called()
    data_manager.file.close.assert_not_called()

def test_close_not_closed(data_manager: DataManager) -> None: 
    """Test the close method when the file has not need closed"""
    file = MagicMock()
    writer = MagicMock()
    data_manager.file = file
    data_manager.writer = writer
    data_manager.file.closed = False
    data_manager.close()
    data_manager.file.flush.assert_called_once()
    data_manager.file.close.assert_called_once()

# ---------------------------------------------------------------------------------------
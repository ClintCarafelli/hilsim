import pytest
from unittest.mock import patch, MagicMock, mock_open
from src.LoadTOML import LoadTOML

path = "/fake/path/to_TOML.TOML"
config_data = {"name": "sensor", "num_measurements": 4}
mock_data = b"fake data"

def test_tomlib_import():
    mock_toml = MagicMock()
    mock_toml.load.return_value = mock_data
    with patch("builtins.open", mock_open(read_data=mock_data)) as mocked_open:
        with patch.dict("sys.modules", {"tomllib": mock_toml}):
            result = LoadTOML(path)
            mocked_open.assert_called_once_with(path, "rb")
            assert result is mock_data

def test_tomli_import():
    mock_toml = MagicMock()
    mock_toml.load.return_value = mock_data
    with patch("builtins.open", mock_open(read_data=mock_data)) as mocked_open:
        with patch("sys.modules", {"tomllib": None}):
            with patch.dict("sys.modules", {"tomli": mock_toml}):
                result = LoadTOML(path)
                mocked_open.assert_called_once_with(path, "rb")
                assert result is mock_data

def test_import_error(): 
    with patch("sys.modules", {"tomllib": None, "tomli": None}):
        with pytest.raises(RuntimeError):
            LoadTOML(path)






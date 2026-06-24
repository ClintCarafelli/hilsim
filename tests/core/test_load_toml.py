"""Test the LoadTOML function"""
import pytest 

from unittest.mock import patch, MagicMock, mock_open
from hilsim.core.load_toml import LoadTOML

# ---------------------------------------------------------------------------------------
# Setup
PATH = "/fake/path/to_TOML.TOML"
CONFIG_DATA = {"name": "sensor", "num_measurements": 4}
MOCK_DATA = b"fake data"

# ---------------------------------------------------------------------------------------
# Test the LoadTOML function

def test_tomlib_import() -> None:
    """Test successfully loading a .toml file"""
    mock_toml = MagicMock()
    mock_toml.load.return_value = MOCK_DATA
    with (patch("builtins.open", mock_open(read_data=MOCK_DATA)) as mocked_open,
          patch.dict("sys.modules", {"tomllib": mock_toml})):
            result = LoadTOML(PATH)
            mocked_open.assert_called_once_with(PATH, "rb")
            assert result is MOCK_DATA

def test_import_error() -> None:
    """Test raising an import error""" 
    with patch.dict("sys.modules", {"tomllib": None}):
        with pytest.raises(RuntimeError, match="No TOML parser found"):
            LoadTOML(PATH)

# ---------------------------------------------------------------------------------------


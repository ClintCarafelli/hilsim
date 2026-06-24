from pathlib import Path

def LoadTOML(path: Path) -> dict:
    """ load TOML file into a dictonary """
    try:
        import tomllib         
    except ImportError:
        raise RuntimeError("No TOML parser found. On Python >= 3.11" \
        " run: pip install tomli.")

    with open(path, "rb") as f:
        config_data = tomllib.load(f)

    return config_data

#--------------------------------------------------------------------
def LoadTOML(path: None | str) -> dict:
    # DESCRIPTION: Load the config.toml file and return a dictonary: 
    #
    # INPUTS: 
    #   - path: type None or string. Path to config file
    #
    # OUTPUTS: 
    #   - config_data: a dictonary of the configuration data

    # Attempt to be compatable with multiple python versions. 
    try:
        try:
            import tomllib         
        except ImportError:
            import tomli as tomllib
    except ImportError:
        raise RuntimeError("No TOML parser found. On Python < 3.11" \
        " run: pip install tomli.")

    with open("config.toml", "rb") as f:
        config_data = tomllib.load(f)

    return config_data
#--------------------------------------------------------------------
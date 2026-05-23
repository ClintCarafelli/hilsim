from src.SCD30Driver import SCD30Driver
from src.BMP388Driver import BMP388Driver
from src.STEMMADriver import STEMMADriver
from src.ME2Driver import ME2Driver
from src.INA260Driver import INA260Driver

# Map the class that drives the sensor to the driver field in the config.toml file
driver_registry: dict = {
    "SCD30_driver":   SCD30Driver,
    "BMP388_driver":  BMP388Driver,
    "STEMMA1_driver": STEMMADriver,
    "STEMMA2_driver": STEMMADriver,
    "STEMMA3_driver": STEMMADriver,
    "ME2_driver":     ME2Driver,
    "INA260_driver":  INA260Driver,
}



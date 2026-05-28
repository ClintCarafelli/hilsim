from src.SCD30Driver import SCD30Driver
from src.BMP388Driver import BMP388Driver
from src.STEMMADriver import STEMMADriver
from src.ME2Driver import ME2Driver
from src.INA260Driver import INA260Driver

from src.FakeINA260 import FakeINA260
from src.FakeBMP388 import FakeBMP388
from src.FakeME2 import FakeME2
from src.FakeSCD30 import FakeSCD30
from src.FakeSTEMMA import FakeSTEMMA


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

fake_sensor_registry: dict = {
    "INA260": FakeINA260,
    "SCD30": FakeSCD30,
    "STEMMA1": FakeSTEMMA,
    "STEMMA2": FakeSTEMMA,
    "STEMMA3": FakeSTEMMA,
    "ME2": FakeME2,
    "BMP388": FakeBMP388
}



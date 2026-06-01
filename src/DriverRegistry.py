from src.scd30_driver import SCD30Driver
from src.bmp388_driver import BMP388Driver
from src.stemma_driver import STEMMADriver
from src.me2_driver import ME2Driver
from src.ina260_driver import INA260Driver

from src.fake_ina260 import FakeINA260
from src.fake_bmp388 import FakeBMP388
from src.fake_me2 import FakeME2
from src.fake_scd30 import FakeSCD30
from src.fake_stemma import FakeSTEMMA


# Map the class that drives the sensor to the driver field in the config.toml file
driver_registry: dict = {
    "STEMMA1_driver": STEMMADriver,
    "STEMMA2_driver": STEMMADriver,
    "STEMMA3_driver": STEMMADriver,
    "SCD30_driver":   SCD30Driver,
    "BMP388_driver":  BMP388Driver,
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



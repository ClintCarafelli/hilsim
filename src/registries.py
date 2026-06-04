from src.scd30 import SCD30Driver, FakeSCD30
from src.bmp388 import BMP388Driver, FakeBMP388
from src.stemma import STEMMADriver, FakeSTEMMA
from src.me2 import ME2Driver, FakeME2
from src.ina260 import INA260Driver, FakeINA260


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



import os 
import logging 
import time
from LoadTOML import LoadTOML
from SensorManager import SensorManager
from pathlib import Path

config_path = Path(__file__).parent.parent / "config.toml"
config_dict = LoadTOML(config_path)
config_dict["main_path"] = os.path.dirname(os.path.abspath(__file__))
i2c_bus = 30

new_logger_name = "test_log.txt"
current_log_handler = logging.basicConfig(filename=new_logger_name,
	level=logging.DEBUG, 
	format='%(asctime)s - %(levelname)s - %(message)s')

manager = SensorManager(config_dict, i2c_bus, True)

#print(f"Active sensors: {manager.enabled_sensors}\n")
manager.initialize_all()
#print(manager.read("SCD30"))

while True:
    print("-"*30 + "Readings" + "-"*30)
    data = manager.read_all()

    for sensor_id, readings in data.items():
        print(f"[{sensor_id}]")
        if readings:
            for r in readings: 
                print(f"    {r.name} {r.value} {r.unit}")
        else: 
            print("NO DATA")

    print()
    time.sleep(2)
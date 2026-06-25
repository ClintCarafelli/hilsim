"""Major file handling parameters, logs and data file handling"""

import atexit
import csv
import logging
import time
from collections.abc import Iterable
from pathlib import Path


class LogManager:
    """Handle the system logging to change out logging files to meet telemetry constraints"""

    def __init__(self):
        self.format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        self.root_logger = None
        self.handler = None

    def start_logging(self):
        """Create the root logger and the first handler"""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        self.root_logger = root_logger
        handler = logging.FileHandler(self._build_log_filename())
        handler.setLevel(logging.INFO)
        handler.setFormatter(self.format)
        self.root_logger.addHandler(handler)
        self.handler = handler

    def switch_files(self):
        """Remove the previous logger and add a new one in its place
        that points to a new file"""
        self.root_logger.removeHandler(self.handler)
        self.handler.close()
        handler = logging.FileHandler(self._build_log_filename())
        handler.setLevel(logging.INFO)
        handler.setFormatter(self.format)
        self.root_logger.addHandler(handler)
        self.handler = handler

    def _build_log_filename(self):
        """Create a file name for a log file, consisting of
        log_(UNIX time when file was started).log"""
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        file_name = log_dir / ("log_" + time.strftime("%Y%m%d_%H%M%S") + ".log")
        return file_name


class DataManager:
    """Handle writing data to csv files"""

    def __init__(
        self,
        output_dir: Path,
        headers: Iterable | list[Iterable],
        data_filename: str | None = None,
    ) -> None:
        file_name = self._resolve_file_name(data_filename)
        self.headers = headers
        self.data_dir = output_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._open_file(file_name)
        self.counter = 0
        atexit.register(self.close)

    def swap_data_file(self, new_data_file_name: str | None = None) -> None:
        """Write data to a new file"""
        file_name = self._resolve_file_name(new_data_file_name)
        self.close()
        self._open_file(file_name)
        self.counter = 0

    def _resolve_file_name(self, filename: str | None) -> str:
        """If no file name given, use current UNIX time"""
        if filename is None:
            filename = time.strftime("%Y%m%d_%H%M%S")
        return filename + ".csv"

    def _open_file(self, filename: str) -> None:
        """Open a new csv file"""
        self.file = open(
            self.data_dir / filename, mode="w", newline="", encoding="utf-8"
        )
        self.writer = csv.writer(self.file)

        for header in self.headers:
            self.writer.writerow(header)
        self.file.flush()

    def add_data_to_file(self, data: dict, time_val: float, n: int | None = None) -> None:
        """Add data to the current file"""

        data_row = []
        for measurements in data.values(): 
            for variable in measurements.values(): 
                  data_row.append(variable.value)
        data_row.append(time_val)
        if n is not None and n <= 0:
            raise ValueError("n must be strictly positive (i.e. > 0)")
        self.writer.writerow(data_row)
        if n is not None:
            self.counter += 1
            if self.counter % n == 0:
                self.file.flush()
        else:
            self.file.flush()

    def close(self) -> None:
        """Close the current data file"""
        if not self.file.closed:
            self.file.flush()
            self.file.close()

    def convert_data_to_str_iterable(self, data: dict, time_val: float) -> list: 
        """convert nested dictonaries of data for printing to rich table"""
        data_row = []
        for measurements in data.values(): 
            for variable in measurements.values(): 
                data_row.append(str(variable.value))
        data_row.append(str(time_val))
        return data_row

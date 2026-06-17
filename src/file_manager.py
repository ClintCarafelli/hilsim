"""Major file handling parameters, logs and data file handling"""

import atexit
import csv
import logging
import time
from collections.abc import Iterable
from pathlib import Path


class HandleLogging:
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
        file_name = "log_" + time.strftime("%Y%m%d_%H%M%S") + ".log"
        return file_name


class HandleData:
    """Handle writing data to csv files"""

    def __init__(
        self,
        output_dir: str,
        header_iterable: Iterable,
        data_file_name: str | None = None,
    ) -> None:
        file_name = self._resolve_file_name(data_file_name)
        self.header = header_iterable
        self.data_dir = Path(output_dir)
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

    def _resolve_file_name(self, file_name: str | None) -> str:
        """If no file name given, use current UNIX time"""
        if file_name is None:
            file_name = time.strftime("%Y%m%d_%H%M%S")
        return file_name

    def _open_file(self, file_name: str) -> None:
        """Open a new csv file"""
        self.file = open(
            self.data_dir / (file_name + ".csv"), mode="w", newline="", encoding="utf-8"
        )
        self.writer = csv.writer(self.file)
        self.writer.writerow(self.header)

    def add_data_to_file(self, data: Iterable, n: int | None = None) -> None:
        """Add data to the current file"""
        if n is not None and n <= 0:
            raise ValueError("n must be strictly positive (i.e. > 0)")
        self.writer.writerow(data)
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

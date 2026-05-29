""" Major file handling parameters, including log and parquet file handling and 
compression for email backup system"""
import logging
import time

class HandleLogging():
    """ Handle the system logging to change out logging files to meet telemetry constraints"""
    def __init__(self):
        self.format      = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.root_logger = None
        self.handler     = None

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
        file_name = "log_" + str(time.time()) + ".log"
        return file_name

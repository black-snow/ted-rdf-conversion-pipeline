import abc
import enum
import logging
import sys
from colorama import Fore

import logstash

from ted_sws import config


class LoggingType(enum.Enum):
    ELK = "ELK"
    PY = "PY"
    DB = "DB"


DOMAIN_LOGGING_TYPES = config.LOGGING_TYPE.split(",") if config.LOGGING_TYPE is not None else [LoggingType.PY.value]
DEFAULT_LOGGER_LEVEL = logging.NOTSET
DEFAULT_LOGGER_NAME = "ROOT"

LOG_ERROR_TEXT = Fore.RED + "{}" + Fore.RESET
LOG_SUCCESS_TEXT = Fore.GREEN + "{}" + Fore.RESET
LOG_INFO_TEXT = Fore.CYAN + "{}" + Fore.RESET
LOG_WARN_TEXT = Fore.YELLOW + "{}" + Fore.RESET

LOG_ERROR_LEVEL = logging.ERROR
LOG_INFO_LEVEL = logging.INFO
LOG_WARN_LEVEL = logging.WARNING


class LoggerABC(abc.ABC):
    """
    This abstract class provides methods definitions and infos for available loggers
    """
    pass


class Logger(LoggerABC):
    """
    This class provides common features for available loggers
    """

    def __init__(self, name: str = DEFAULT_LOGGER_NAME, level: int = DEFAULT_LOGGER_LEVEL):
        self.level = level
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        if self.has_logging_type(LoggingType.ELK):
            self.add_elk_handler()

    def get_logger(self) -> logging.Logger:
        return self.logger

    @staticmethod
    def has_logging_type(logging_type: LoggingType):
        return logging_type.value in DOMAIN_LOGGING_TYPES

    def add_stdout_handler(self, level: int = DEFAULT_LOGGER_LEVEL, formatter: logging.Formatter = None):
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(level)
        if formatter is not None:
            console.setFormatter(formatter)
        self.logger.addHandler(console)

    def add_elk_handler(self, level: int = DEFAULT_LOGGER_LEVEL):
        host = config.ELK_HOST
        port = config.ELK_PORT
        version = config.ELK_VERSION

        elk = logstash.LogstashHandler(host, port, version=version)
        elk.setLevel(level)
        self.logger.addHandler(elk)
        # self.logger.addHandler(logstash.TCPLogstashHandler(host, port, version=version))

    def log(self, msg: str, level: int = None):
        self.logger.log(level if level is not None else self.level, msg)


logger = Logger()
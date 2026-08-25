"""
The logging setup for the whole app lives here.
"""

import logging
import logging.handlers
import os
from pathlib import Path


LOGGER_NAME = "pixvault"
MAX_BYTES = 1000000
BACKUP_COUNT = 3
LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"


def logDirectory() -> Path:
    """Returns the folder logs are written into, under the user's app data rather than the project folder so a packaged .exe can still write to it."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
    else:
        base = os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state"
    return (Path(base) / "PixVault" / "logs").resolve() # resolve, or the Store build of Python reports a path it is not really writing to


def logFilePath() -> Path:
    """The file this run is writing to."""
    return logDirectory() / "pixvault.log"


def fileHandler(level: int) -> logging.Handler | None:
    """Builds the file handler, returning None if the file will not open. A log we cannot write is not a reason to stop the app starting."""
    try:
        logDirectory().mkdir(parents=True, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(logFilePath(), maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8")
    except OSError as e:
        print(f"Could not open the log file at {logFilePath()}, logging to the console only: {e}")
        return None
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    return handler


def setupLogging(consoleLevel: int = logging.INFO, fileLevel: int = logging.DEBUG, logToFile: bool = True) -> logging.Logger:
    """Wires up the handlers the app logs through, called once from main().
    The console gets the readable summary, the file gets the detail.
    Set PIXVAULT_DEBUG=1 to turn the console up for a noisy run."""
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers: # already set up
        return logger

    if os.environ.get("PIXVAULT_DEBUG"):
        consoleLevel = logging.DEBUG

    console = logging.StreamHandler()
    console.setLevel(consoleLevel)
    console.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console)

    if logToFile:
        handler = fileHandler(fileLevel)
        if handler is not None:
            logger.addHandler(handler)

    logger.setLevel(min(handler.level for handler in logger.handlers)) # or the logger filters records out before a handler sees them
    logger.propagate = False
    logger.debug("Logging started, writing to %s", logFilePath())
    return logger


def getLogger(name: str) -> logging.Logger:
    """Returns the logger for a module, called as getLogger(__name__) so "device.adb"
    becomes "pixvault.device.adb"."""
    if name in (LOGGER_NAME, "__main__"): # same as saying if name == string or name == string 
        return logging.getLogger(LOGGER_NAME)
    return logging.getLogger(f"{LOGGER_NAME}.{name}")
"""
Logging system.
"""
import logging
import os.path

log_dir = os.path.abspath('./logs/')
FORMAT: str = "%(asctime)s %(name)s %(levelname)s %(message)s"


def make_logger(name: str,
                logfilename: str,
                level: int = logging.DEBUG) -> logging.Logger:

    formatter = logging.Formatter(FORMAT)
    path: str = os.path.join(log_dir, logfilename)

    handler = logging.FileHandler(path, mode='w')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

"""Robust logger wrapper.

Provides seamless fallback to standard library logging if loguru is absent.
"""

import sys

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger("WeatherForecastDS")
    if not logger.handlers:
        _h = logging.StreamHandler(sys.stdout)
        _h.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s"))
        logger.addHandler(_h)
        logger.setLevel(logging.INFO)

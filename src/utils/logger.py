# project_root/src/utils/logger.py
"""
Sets up a logger for the application.
"""

import logging
import sys

# You can customize the logging format and level here
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("reposcan")


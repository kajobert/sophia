import logging
import os
from logging.handlers import RotatingFileHandler

# Define the path for the log directory and log file
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "sophia.log")

# Create the log directory if it doesn't exist
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Create a logger instance
logger = logging.getLogger("sophia")
logger.setLevel(logging.DEBUG)  # Set the lowest level to capture all messages

# Create a formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create a file handler with log rotation
# Rotates logs when they reach 2MB, keeping 5 backup logs.
file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=5
)
file_handler.setLevel(logging.DEBUG)  # Log everything to the file
file_handler.setFormatter(formatter)

# Create a stream handler to output to the console
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)  # Log INFO and above to the console
stream_handler.setFormatter(formatter)

# Add the handlers to the logger
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

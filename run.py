import uvicorn
import logging
import sys

def setup_logging():
    """
    Sets up a robust, unified logging configuration.
    This ensures that logs from all modules are captured and displayed correctly,
    bypassing any potential quirks of how Uvicorn handles logging.
    """
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove any existing handlers to avoid duplicate logs
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Create a handler to write logs to standard output (what you see in `docker logs`)
    handler = logging.StreamHandler(sys.stdout)

    # Create a formatter and set it for the handler
    # This format is detailed and easy to read.
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
    )
    handler.setFormatter(formatter)

    # Add the handler to the root logger
    root_logger.addHandler(handler)

    logging.info("="*50)
    logging.info("Logging configured programmatically from run.py")
    logging.info("="*50)

if __name__ == "__main__":
    # 1. Set up logging BEFORE anything else happens.
    setup_logging()

    # 2. Programmatically run the Uvicorn server.
    # We use reload=False because in a Docker container, we don't need auto-reloading.
    # The host and port are the same as before.
    uvicorn.run(
        "backend.server:app",
        host="0.0.0.0",
        port=8080,
        log_level="info", # Uvicorn's log level
        reload=False
    )

import uvicorn
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Programmatically configures and runs the Uvicorn server.
    This provides a more robust way to manage configurations for different environments
    (e.g., development vs. testing) than relying on CLI flags.
    """
    # Default to 'development' if SOPHIA_ENV is not set
    env = os.getenv('SOPHIA_ENV', 'development')

    # --- Configuration ---
    app_module = "web.api:app"
    host = "127.0.0.1"
    port = 8000
    reload = False

    if env == 'development':
        logging.info("Starting server in DEVELOPMENT mode with auto-reload enabled.")
        reload = True
    elif env == 'test':
        logging.info("Starting server in TEST mode. Auto-reload is disabled.")
        # In test mode, we don't want the server to reload.
        # The test runner will manage the server's lifecycle.
        # The 'test' env var is primarily for the web.api module to apply mocks.
        pass
    else:
        logging.info(f"Starting server in PRODUCTION-LIKE mode ('{env}'). Auto-reload is disabled.")

    uvicorn.run(
        app_module,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()

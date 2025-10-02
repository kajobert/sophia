import subprocess
import time
import os
import logging

# --- Configuration ---
TUI_APP_PATH = "tui/app.py"
CRASH_LOG_PATH = "logs/crash.log"
LAST_GOOD_COMMIT_FILE = ".last_known_good_commit"
MAX_RESTART_ATTEMPTS = 3  # Max consecutive failures before a rollback is triggered
RESTART_DELAY_SECONDS = 5  # Delay before restarting the app after a crash
INITIAL_KNOWN_GOOD_COMMIT = "f7c727c852fe2937b9508c007a1ece6b7319355d"

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="[Guardian] %(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/guardian.log"),
    ]
)

def get_last_known_good_commit() -> str:
    """Reads the last known good commit hash from the state file."""
    if not os.path.exists(LAST_GOOD_COMMIT_FILE):
        logging.info(f"'{LAST_GOOD_COMMIT_FILE}' not found, using initial known good commit.")
        with open(LAST_GOOD_COMMIT_FILE, "w") as f:
            f.write(INITIAL_KNOWN_GOOD_COMMIT)
        return INITIAL_KNOWN_GOOD_COMMIT
    with open(LAST_GOOD_COMMIT_FILE, "r") as f:
        return f.read().strip()

def revert_to_last_known_good():
    """Performs a hard reset to the last known good commit."""
    commit_hash = get_last_known_good_commit()
    logging.warning(f"Attempting to roll back to commit: {commit_hash}")
    try:
        # Reset all changes to tracked files
        subprocess.run(["git", "reset", "--hard", commit_hash], check=True, capture_output=True, text=True)
        # Remove all untracked files and directories
        subprocess.run(["git", "clean", "-dfx"], check=True, capture_output=True, text=True)
        logging.info(f"Successfully rolled back to commit {commit_hash}.")
    except subprocess.CalledProcessError as e:
        logging.error(f"FATAL: Git rollback failed!")
        logging.error(f"Stderr: {e.stderr}")
        logging.error(f"Stdout: {e.stdout}")
        # If rollback fails, we are in a bad state. Exit to prevent loops.
        exit(1)

def main():
    """Main guardian loop to run and monitor the TUI application."""
    consecutive_failures = 0

    while True:
        logging.info(f"Starting TUI application: {TUI_APP_PATH}")
        process = subprocess.run(
            ["python", TUI_APP_PATH],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if process.returncode == 0:
            logging.info("Application exited cleanly (code 0). Guardian shutting down.")
            break  # User likely exited the app normally

        # --- Crash Detected ---
        consecutive_failures += 1
        logging.error(f"Application crashed with exit code {process.returncode}. This is failure #{consecutive_failures}.")

        # Log the error output
        os.makedirs(os.path.dirname(CRASH_LOG_PATH), exist_ok=True)
        with open(CRASH_LOG_PATH, "w", encoding='utf-8') as f:
            f.write("--- STDOUT ---\n")
            f.write(process.stdout)
            f.write("\n\n--- STDERR ---\n")
            f.write(process.stderr)
        logging.info(f"Crash log saved to {CRASH_LOG_PATH}")

        # Check for rollback condition
        if consecutive_failures >= MAX_RESTART_ATTEMPTS:
            logging.warning(f"Reached {MAX_RESTART_ATTEMPTS} consecutive failures. Triggering rollback.")
            revert_to_last_known_good()
            consecutive_failures = 0  # Reset counter after rollback

        logging.info(f"Restarting application in {RESTART_DELAY_SECONDS} seconds...")
        time.sleep(RESTART_DELAY_SECONDS)

if __name__ == "__main__":
    # Ensure the logs directory exists on startup
    os.makedirs("logs", exist_ok=True)
    main()
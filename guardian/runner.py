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
    """
    Reads the last known good commit hash from the state file.
    If the file doesn't exist, it initializes it with the current HEAD commit.
    """
    if not os.path.exists(LAST_GOOD_COMMIT_FILE):
        logging.warning(f"'{LAST_GOOD_COMMIT_FILE}' not found. Initializing with current HEAD.")
        try:
            # Dynamically get the current commit hash
            current_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True, capture_output=True, text=True
            ).stdout.strip()

            with open(LAST_GOOD_COMMIT_FILE, "w") as f:
                f.write(current_commit)
            logging.info(f"Initialized '{LAST_GOOD_COMMIT_FILE}' with commit: {current_commit}")
            return current_commit
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logging.error(f"FATAL: Could not initialize last known good commit from git. Error: {e}")
            # If git fails, we cannot proceed with self-healing. Exit.
            exit(1)

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
    """
    Main guardian loop to run and monitor the TUI application.
    It simply launches the TUI and checks its exit code. The TUI is responsible
    for logging its own crashes, ensuring full interactivity.
    """
    consecutive_failures = 0

    while True:
        logging.info(f"Starting TUI application: {TUI_APP_PATH}")

        # Run the TUI process, allowing it to inherit stdin, stdout, and stderr
        # to ensure full interactivity. We only need the return code.
        process = subprocess.run(["python", TUI_APP_PATH])

        if process.returncode == 0:
            logging.info("Application exited cleanly (code 0). Guardian shutting down.")
            break  # User likely exited the app normally

        # --- Crash Detected ---
        # A non-zero return code indicates a crash.
        # The TUI app is expected to have logged the crash details itself.
        consecutive_failures += 1
        logging.error(f"Application crashed with exit code {process.returncode}. This is failure #{consecutive_failures}.")
        logging.info(f"A crash log should have been created by the TUI application at '{CRASH_LOG_PATH}'.")

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
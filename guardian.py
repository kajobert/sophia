import subprocess
import time
import sys

def run_main_script():
    """
    Runs main.py as a subprocess and monitors its execution.
    Returns the process's exit code.
    """
    try:
        # We use Popen to allow for more flexible interaction in the future if needed,
        # but for now, we just wait for it to complete.
        process = subprocess.Popen([sys.executable, 'main.py'])
        process.wait()  # Wait for the subprocess to complete
        return process.returncode
    except subprocess.CalledProcessError as e:
        print(f"Guardian: main.py exited with a CalledProcessError: {e}")
        return e.returncode
    except FileNotFoundError:
        print("Guardian Error: 'main.py' or the python interpreter not found.")
        # Return a specific code for this fatal error
        return -1
    except Exception as e:
        print(f"Guardian: An unexpected error occurred while running main.py: {e}")
        return 1 # Generic error code

if __name__ == "__main__":
    while True:
        print("--- Guardian: Starting Sophia (main.py) ---")
        exit_code = run_main_script()

        if exit_code == 0:
            # This can happen if the user types 'exit'
            print("--- Guardian: main.py exited cleanly. Restarting after a short delay... ---")
        else:
            print(f"--- Guardian: main.py crashed with exit code {exit_code}. Performing recovery! ---")

            # 1. Log the error
            try:
                import datetime
                timestamp = datetime.datetime.now().isoformat()
                with open("SOS.log", "a", encoding="utf-8") as f:
                    f.write(f"{timestamp} - CRITICAL: main.py crashed with exit code {exit_code}. Performing git reset.\n")
            except Exception as e:
                print(f"Guardian: Failed to write to SOS.log: {e}")

            # 2. Perform git reset
            try:
                print("Guardian: Attempting to roll back changes with 'git reset --hard HEAD'...")
                reset_result = subprocess.run(['git', 'reset', '--hard', 'HEAD'], check=True, capture_output=True, text=True)
                print(f"Guardian: Git reset successful. Output:\n{reset_result.stdout}")
            except subprocess.CalledProcessError as e:
                print(f"Guardian: CRITICAL FAILURE - Git reset failed with exit code {e.returncode}.")
                print(f"Guardian: Stderr: {e.stderr}")
                print("Guardian: Cannot recover automatically. Please intervene manually. Exiting.")
                sys.exit(1) # Exit guardian if it can't recover
            except FileNotFoundError:
                print("Guardian: CRITICAL FAILURE - 'git' command not found. Cannot perform rollback.")
                print("Guardian: Cannot recover automatically. Please intervene manually. Exiting.")
                sys.exit(1)

        print("--- Guardian: Waiting for 5 seconds before restarting... ---")
        time.sleep(5)

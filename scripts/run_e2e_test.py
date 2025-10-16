import subprocess
import time
import httpx
import os
import sys

# --- Configuration ---
API_BASE_URL = "http://localhost:8080/api/v1"
HEALTH_CHECK_URL = f"{API_BASE_URL}/health/ping"
MISSIONS_URL = f"{API_BASE_URL}/missions"
DOCKER_COMPOSE_FILE = "docker-compose.yml"
SANDBOX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sandbox")
SUMMARY_FILE_PATH = os.path.join(SANDBOX_DIR, "summary.txt")

# API key is read from environment variables for security
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# --- Helper Functions ---

def print_header(message):
    """Prints a formatted header."""
    print("\n" + "="*60)
    print(f"    {message}")
    print("="*60)

def run_command(command, env=None):
    """Runs a command and returns its output."""
    print(f"Executing: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"Error running command: {' '.join(command)}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        raise RuntimeError(f"Command failed: {' '.join(command)}")
    return result

def setup_environment():
    """Starts the Docker environment in detached mode."""
    print_header("Setting up E2E Test Environment")

    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY environment variable not set.")
        sys.exit(1)

    # Ensure the summary file doesn't exist from a previous run
    if os.path.exists(SUMMARY_FILE_PATH):
        os.remove(SUMMARY_FILE_PATH)
        print(f"Removed existing summary file: {SUMMARY_FILE_PATH}")

    # Set up environment variables for docker-compose
    env = os.environ.copy()
    env["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY

    # Using the main docker-compose.yml as discovered during exploration
    command = ["docker", "compose", "-f", DOCKER_COMPOSE_FILE, "up", "-d", "--build"]
    run_command(command, env=env)
    print("Docker environment started.")

def cleanup_environment():
    """Stops and removes the Docker environment."""
    print_header("Cleaning up E2E Test Environment")
    command = ["docker", "compose", "-f", DOCKER_COMPOSE_FILE, "down", "--volumes"]
    try:
        run_command(command)
        print("Docker environment stopped and cleaned up.")
    except RuntimeError as e:
        print(f"Could not clean up environment, please do it manually. Error: {e}")

def wait_for_backend(timeout=180, interval=5):
    """Waits for the backend API to become available."""
    print_header("Waiting for Backend API")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(HEALTH_CHECK_URL, timeout=10)
            if response.status_code == 200:
                print(f"Backend is healthy! (Status: {response.status_code})")
                return True
        except httpx.RequestError as e:
            print(f"Waiting for backend... ({e.__class__.__name__})")
        time.sleep(interval)
    print("Error: Backend did not become available within the timeout period.")
    return False

def run_test_mission():
    """Submits the test mission to the backend."""
    print_header("Submitting Test Mission")
    mission_payload = {
        "description": "Read the README.md file and create a summary of it in /sandbox/summary.txt."
    }
    try:
        response = httpx.post(MISSIONS_URL, json=mission_payload, timeout=30)
        response.raise_for_status()
        mission_id = response.json().get("mission_id")
        print(f"Mission submitted successfully. Mission ID: {mission_id}")
        return mission_id
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        print(f"Error submitting mission: {e}")
        return None

def monitor_and_verify(timeout=300, interval=10):
    """Monitors logs and verifies the outcome of the mission."""
    print_header("Monitoring Mission Progress & Verifying Outcome")
    start_time = time.time()

    while time.time() - start_time < timeout:
        print(f"Checking logs... (Elapsed: {int(time.time() - start_time)}s)")
        logs = run_command(["docker", "compose", "-f", DOCKER_COMPOSE_FILE, "logs", "backend"]).stdout

        if "MISSION COMPLETE" in logs:
            print("Success marker 'MISSION COMPLETE' found in logs.")

            # Allow a moment for the file system to sync
            time.sleep(5)

            print("Verifying output file...")
            if os.path.exists(SUMMARY_FILE_PATH):
                with open(SUMMARY_FILE_PATH, 'r') as f:
                    content = f.read()
                if content.strip():
                    print(f"SUCCESS: Output file '{SUMMARY_FILE_PATH}' created and is not empty.")
                    return True
                else:
                    print(f"FAILURE: Output file '{SUMMARY_FILE_PATH}' was created but is empty.")
                    return False
            else:
                print(f"FAILURE: Output file '{SUMMARY_FILE_PATH}' was not created.")
                return False

        if "HANDLING_ERROR" in logs:
            print("Failure marker 'HANDLING_ERROR' found in logs.")
            return False

        time.sleep(interval)

    print("Error: Mission did not complete within the timeout period.")
    return False

# --- Main Execution ---

def main():
    """Main function to orchestrate the E2E test."""
    try:
        setup_environment()
        if not wait_for_backend():
            sys.exit(1)

        mission_id = run_test_mission()
        if not mission_id:
            sys.exit(1)

        if monitor_and_verify():
            print_header("E2E Test PASSED")
            sys.exit(0)
        else:
            print_header("E2E Test FAILED")
            sys.exit(1)

    finally:
        cleanup_environment()

if __name__ == "__main__":
    main()
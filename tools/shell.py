import subprocess

def run_in_bash_session(command: str) -> str:
    """
    Runs the given bash command in the project's root directory.
    Captures and returns both stdout and stderr.
    """
    try:
        process = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd="." # Ensure command runs from the project root
        )
        output = process.stdout
        if process.stderr:
            output += "\n--- STDERR ---\n" + process.stderr
        return output.strip()
    except subprocess.CalledProcessError as e:
        error_message = f"Command failed with exit code {e.returncode}.\n"
        error_message += f"--- STDOUT ---\n{e.stdout}\n"
        error_message += f"--- STDERR ---\n{e.stderr}"
        return error_message.strip()
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 60 seconds."
    except Exception as e:
        return f"An unexpected error occurred: {e}"
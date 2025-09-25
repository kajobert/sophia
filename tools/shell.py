import subprocess

def run_in_bash_session(command: str) -> str:
    """
    Runs the given bash command.
    """
    try:
        process = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Command failed with exit code {e.returncode}:\n{e.stderr.strip()}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
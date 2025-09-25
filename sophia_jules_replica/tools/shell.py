import subprocess

def run_in_bash_session(command: str) -> str:
    """
    Runs the given bash command in the sandbox.
    Captures and returns both stdout and stderr.
    """
    try:
        # Spuštění příkazu v shellu
        process = subprocess.run(
            command,
            shell=True,
            check=True,  # Vyhodí chybu, pokud příkaz selže
            capture_output=True,
            text=True,
            timeout=30  # Přidání timeoutu pro bezpečnost
        )
        # Kombinace stdout a stderr pro kompletní výstup
        output = process.stdout
        if process.stderr:
            output += "\n--- STDERR ---\n" + process.stderr
        return output.strip()
    except subprocess.CalledProcessError as e:
        # Pokud příkaz selže (non-zero exit code)
        error_message = f"Command failed with exit code {e.returncode}.\n"
        error_message += f"--- STDOUT ---\n{e.stdout}\n"
        error_message += f"--- STDERR ---\n{e.stderr}"
        return error_message.strip()
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"An unexpected error occurred: {e}"
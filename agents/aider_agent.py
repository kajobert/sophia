"""
AiderAgent: Wrapper pro Aider IDE jako autonomní evoluční motor Sophia V4

- Komunikuje s Aider IDE přes CLI (subprocess)
- Omezuje všechny operace na /sandbox
- Validuje a auditovat změny (git log, Ethos module)
- Protokol úkolů: JSON přes stdin/stdout (příprava na REST)
"""
import subprocess
import json
import os
from typing import Any, Dict, Optional

# Přidání cesty k `tools` modulu
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.ethical_reviewer import EthicalReviewTool

AIDER_CLI_PATH = "aider"  # předpokládá se v $PATH, případně upravit
SANDBOX_PATH = os.path.abspath("./sandbox")

class AiderAgent:
    def __init__(self, sandbox_path: str = SANDBOX_PATH, aider_cli: str = AIDER_CLI_PATH):
        self.sandbox_path = sandbox_path
        self.aider_cli = aider_cli
        assert os.path.isdir(self.sandbox_path), f"Sandbox {self.sandbox_path} neexistuje!"

    def run_aider(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Spustí Aider CLI s úkolem (JSON stdin), vrací výstup (JSON stdout)."""
        proc = subprocess.Popen(
            [self.aider_cli, "--json"],
            cwd=self.sandbox_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        input_json = json.dumps(task)
        out, err = proc.communicate(input=input_json)
        if proc.returncode != 0:
            raise RuntimeError(f"Aider CLI selhalo: {err}")
        return json.loads(out)

    def propose_change(self, description: str, files: Optional[list] = None) -> Dict[str, Any]:
        """Navrhne a provede změnu v sandboxu dle popisu."""
        task = {"action": "propose_change", "description": description, "files": files or []}
        result = self.run_aider(task)
        self._audit_change()
        return result

    def _audit_change(self):
        """Audituje změny v sandboxu (git diff, validace Ethos modulem)."""
        try:
            # Fáze 1: Přidání všech změn do stage pro audit
            subprocess.run(["git", "add", "."], cwd=self.sandbox_path, check=True)

            # Fáze 2: Získání diffu změn v sandboxu
            diff_process = subprocess.run(
                ["git", "diff", "--staged"],
                cwd=self.sandbox_path,
                capture_output=True,
                text=True,
                check=True
            )
            change_diff = diff_process.stdout

            if not change_diff.strip():
                print("No changes to audit.")
                return

            # Fáze 3: Etická revize
            ethical_reviewer = EthicalReviewTool()
            review_result = ethical_reviewer._run(plan=f"Review the following code changes:\n\n{change_diff}")
            print(f"Ethical Review Result: {review_result}")

            # Fáze 4: Rozhodnutí
            if "decision: pass" not in review_result.lower():
                # Pokud revize selže, vrátíme změny zpět
                print(f"Ethical review failed. Reverting changes. Reason: {review_result}")
                subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=self.sandbox_path, check=True)
                raise RuntimeError(f"Ethical review failed. Changes reverted.")

            # Fáze 5: Commit, pokud revize projde
            print("Ethical review passed. Committing changes.")
            subprocess.run(["git", "commit", "-m", "Autonomously generated change"], cwd=self.sandbox_path, check=True)

        except subprocess.CalledProcessError as e:
            # Pokud jakýkoliv git příkaz selže, revertujeme
            print(f"A git command failed during audit. Reverting changes. Error: {e.stderr}")
            subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=self.sandbox_path, check=True)
            raise RuntimeError(f"A git command failed during the audit process. Changes reverted.")
        except Exception as e:
            # Jakákoliv jiná chyba by měla také vést k vrácení změn
            print(f"An unexpected error occurred during audit. Reverting changes. Error: {e}")
            subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=self.sandbox_path, check=True)
            raise RuntimeError(f"An unexpected error occurred during audit. Changes reverted.")

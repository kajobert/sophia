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

AIDER_CLI_PATH = "aider"  # předpokládá se v $PATH, případně upravit
SANDBOX_PATH = os.path.abspath("./sandbox")


class AiderAgent:
    def __init__(
        self, sandbox_path: str = SANDBOX_PATH, aider_cli: str = AIDER_CLI_PATH
    ):
        self.sandbox_path = sandbox_path
        self.aider_cli = aider_cli
        assert os.path.isdir(self.sandbox_path), (
            f"Sandbox {self.sandbox_path} neexistuje!"
        )

    def run_aider(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Spustí Aider CLI s úkolem (JSON stdin), vrací výstup (JSON stdout)."""
        proc = subprocess.Popen(
            [self.aider_cli, "--json"],
            cwd=self.sandbox_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        input_json = json.dumps(task)
        out, err = proc.communicate(input=input_json)
        if proc.returncode != 0:
            raise RuntimeError(f"Aider CLI selhalo: {err}")
        return json.loads(out)

    def propose_change(
        self, description: str, files: Optional[list] = None
    ) -> Dict[str, Any]:
        """Navrhne a provede změnu v sandboxu dle popisu."""
        task = {
            "action": "propose_change",
            "description": description,
            "files": files or [],
        }
        result = self.run_aider(task)
        self._audit_change()
        return result

    def _audit_change(self):
        """Audituje změny v sandboxu (git log, validace Ethos modulem)."""
        import subprocess
        from core.ethos_module import EthosModule

        # Získání posledního commitu v sandboxu
        try:
            git_log = subprocess.check_output(
                ["git", "--no-pager", "log", "-1", "--pretty=%B"],
                cwd=self.sandbox_path,
                text=True,
            )
        except Exception as e:
            raise RuntimeError(f"Nelze získat git log v sandboxu: {e}")

        # Validace commit message Ethos modulem
        ethos = EthosModule()
        result = ethos.evaluate(git_log.strip())
        if result["decision"] != "approve":
            raise RuntimeError(
                f"Změna v sandboxu nebyla eticky schválena: {result['feedback']}"
            )
        # TODO: Možnost review jiným agentem (Philosopher/Architect) lze přidat zde

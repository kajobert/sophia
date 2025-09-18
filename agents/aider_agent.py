import subprocess
import json
import os
from typing import Any, Dict, Optional
from core.agent_config import load_agent_config

class AiderAgent:
    """
    Wrapper pro Aider IDE.
    - Komunikuje s Aider IDE přes CLI (subprocess) pomocí JSON-RPC.
    - Omezuje všechny operace na /sandbox.
    """
    def __init__(self):
        agent_config = load_agent_config("aider")
        self.sandbox_path = os.path.abspath(agent_config.get("sandbox_path", "./sandbox"))
        self.aider_cli = agent_config.get("cli_path", "aider")

        if not os.path.isdir(self.sandbox_path):
            raise FileNotFoundError(f"Adresář sandboxu '{self.sandbox_path}' neexistuje!")

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
        """Audituje změny v sandboxu (git log, validace Ethos modulem)."""
        # TODO: Integrace s Ethos modulem, review, git log atd.
        pass

import os
from crewai.tools import BaseTool

class DirectoryCreationTool(BaseTool):
    """
    Nástroj pro vytváření nových adresářů na zadané cestě.
    """
    def __init__(self):
        super().__init__(
            name="Directory Creation Tool",
            description="Vytváří nový adresář na zadané cestě. Přijímá argument 'directory_path'."
        )

    def _run(self, directory_path: str) -> dict:
        """
        Vytvoří nový adresář.

        Args:
            directory_path (str): Cesta k adresáři, který má být vytvořen.

        Returns:
            dict: Slovník s informacemi o výsledku operace,
                  např. úspěch/neúspěch a chybová zpráva.
        """
        try:
            # Použití exist_ok=True zabrání chybě, pokud adresář již existuje
            os.makedirs(directory_path, exist_ok=True)
            return {"status": "success", "message": f"Adresář '{directory_path}' byl úspěšně vytvořen nebo již existuje."}
        except OSError as e:
            # Zachytí chyby operačního systému, např. nedostatečná oprávnění
            return {"status": "error", "message": f"Nepodařilo se vytvořit adresář '{directory_path}': {e}"}
        except Exception as e:
            # Zachytí jakékoli jiné neočekávané chyby
            return {"status": "error", "message": f"Došlo k neočekávané chybě při vytváření adresáře '{directory_path}': {e}"}
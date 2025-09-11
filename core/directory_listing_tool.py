import os
from crewai.tools import BaseTool

class DirectoryListingTool(BaseTool):
    name: str = "Directory Listing Tool"
    description: str = "Vypíše obsah zadaného adresáře (soubory i složky)."

    def _run(self, directory_path: str) -> list[str]:
        """
        Vypíše obsah zadaného adresáře (soubory i složky).
        """
        try:
            return os.listdir(directory_path)
        except FileNotFoundError:
            return [f"Chyba: Adresář '{directory_path}' nebyl nalezen."]
        except Exception as e:
            return [f"Nastala chyba při čtení adresáře: {e}"]

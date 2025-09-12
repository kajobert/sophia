import os

def directory_creation_tool(directory_path: str) -> dict:
    """Vytváří nový adresář na zadané cestě. Přijímá argument 'directory_path'."""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return {"status": "success", "message": f"Adresář '{directory_path}' byl úspěšně vytvořen nebo již existuje."}
    except OSError as e:
        return {"status": "error", "message": f"Nepodařilo se vytvořit adresář '{directory_path}': {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Došlo k neočekávané chybě při vytváření adresáře '{directory_path}': {e}"}


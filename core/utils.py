import json
import datetime


import os
import importlib
import inspect
from typing import List, Dict, Any
from tools.base_tool import BaseTool

class CustomJSONEncoder(json.JSONEncoder):
    """
    Vlastní JSON enkodér, který správně serializuje objekty 'datetime'.
    """

    def default(self, obj):
        """
        Přetížená metoda pro zpracování typů, které standardní enkodér neumí.
        """
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)

def list_tools() -> List[Dict[str, Any]]:
    """
    Dynamicky načte všechny nástroje ze složky 'tools' a vrátí jejich popis.
    """
    tools_data = []
    tools_dir = "tools"
    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = f"tools.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                for name, cls in inspect.getmembers(module, inspect.isclass):
                    if issubclass(cls, BaseTool) and cls is not BaseTool and not inspect.isabstract(cls):
                        try:
                            instance = cls()
                            # Získáme parametry z Pydantic schématu
                            params = {}
                            if hasattr(instance, 'args_schema') and hasattr(instance.args_schema, 'model_fields'):
                                params = {name: field.annotation.__name__ for name, field in instance.args_schema.model_fields.items()}

                            tools_data.append({
                                "name": name,
                                "description": instance.description,
                                "parameters": params
                            })
                        except Exception:
                            # Ignorujeme nástroje, které nelze instanciovat bez argumentů
                            pass
            except Exception:
                # Ignorujeme moduly, které se nepodaří načíst
                pass
    return tools_data

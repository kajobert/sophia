import json
import datetime


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

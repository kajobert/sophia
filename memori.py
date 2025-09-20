# Robustní mock pro modul memori

class Memori:
    """
    Mock třída pro simulaci persistentní paměti (Memori API/SDK).
    Sleduje volání, umožňuje simulovat chyby a vracet testovací data.
    """
    def __init__(self):
        self.calls = []
        self.memory = {}
        self.raise_on = set()

    def set_raise(self, method_name):
        self.raise_on.add(method_name)

    def clear_raise(self, method_name):
        self.raise_on.discard(method_name)

    def store(self, key, value):
        self.calls.append(("store", key, value))
        if "store" in self.raise_on:
            raise Exception("Mocked store error")
        self.memory[key] = value
        return True

    def retrieve(self, key):
        self.calls.append(("retrieve", key))
        if "retrieve" in self.raise_on:
            raise Exception("Mocked retrieve error")
        return self.memory.get(key, None)

    def delete(self, key):
        self.calls.append(("delete", key))
        if "delete" in self.raise_on:
            raise Exception("Mocked delete error")
        return self.memory.pop(key, None)

    def get_calls(self):
        return self.calls

# Pro kompatibilitu s původním importem
memori = Memori

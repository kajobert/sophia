# /memory/semantic_memory.py
"""
Modul pro správu sémantické paměti Sophie.
Tato paměť ukládá abstrahované znalosti a koncepty jako vektorové reprezentace.
Využívá ChromaDB pro efektivní vyhledávání na základě podobnosti.
"""

import chromadb
import os
import shutil

class SemanticMemory:
    """
    Třída pro správu sémantické paměti pomocí ChromaDB.
    """
    def __init__(self, db_path='memory/sophia_semantic_db', collection_name='sophia_main_memory'):
        """
        Inicializuje klienta ChromaDB a načte nebo vytvoří kolekci.
        """
        # Zajistíme, že adresář pro databázi existuje
        os.makedirs(db_path, exist_ok=True)

        self.client = chromadb.PersistentClient(path=db_path)
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def add_memory(self, document, memory_id, metadata=None):
        """
        Přidá novou vzpomínku (dokument) do ChromaDB.
        Metadata musí obsahovat 'weight' a 'ethos_coefficient'.

        Args:
            document (str): Textový obsah vzpomínky.
            memory_id (str): Unikátní ID pro tuto vzpomínku.
            metadata (dict, optional): Slovník s metadaty. Defaults to None.
        """
        if metadata is None:
            metadata = {}

        # Zajistíme, že povinná metadata existují
        metadata.setdefault('weight', 1.0)
        metadata.setdefault('ethos_coefficient', 0.0)

        # ChromaDB vyžaduje, aby ID bylo ve formátu string
        if not isinstance(memory_id, str):
            memory_id = str(memory_id)

        self.collection.add(
            documents=[document],
            metadatas=[metadata],
            ids=[memory_id]
        )

    def access_memory(self, memory_id):
        """
        Načte vzpomínku a zvýší její váhu o 0.1.

        Args:
            memory_id (str): ID vzpomínky, ke které se přistupuje.

        Returns:
            dict: Slovník s metadaty vzpomínky, nebo None, pokud nebyla nalezena.
        """
        if not isinstance(memory_id, str):
            memory_id = str(memory_id)

        # Načteme vzpomínku podle ID
        memory = self.collection.get(ids=[memory_id])

        if memory and memory['ids']:
            current_metadata = memory['metadatas'][0]

            # Zvýšíme váhu
            new_weight = current_metadata.get('weight', 1.0) + 0.1
            current_metadata['weight'] = new_weight

            # Aktualizujeme záznam v ChromaDB
            self.collection.update(
                ids=[memory_id],
                metadatas=[current_metadata]
            )

            return current_metadata
        else:
            return None

    def memory_decay(self):
        """
        Placeholder pro budoucí implementaci mechanismu blednutí vzpomínek.
        """
        pass

# Tento blok slouží pro případné budoucí testování nebo ukázku použití.
if __name__ == '__main__':
    # Vytvoření instance paměti (vytvoří adresář sophia_semantic_db, pokud neexistuje)
    sm = SemanticMemory()

    # Přidání testovací vzpomínky
    test_id = "test_concept_001"
    sm.add_memory(
        document="Testovací koncept pro sémantickou paměť.",
        memory_id=test_id,
        metadata={"category": "testing"}
    )
    print(f"Přidána vzpomínka s ID: {test_id}")

    # Přístup ke vzpomínce pro zvýšení váhy
    retrieved_meta = sm.access_memory(test_id)
    print(f"Načtená metadata (po 1. přístupu): {retrieved_meta}")

    retrieved_meta = sm.access_memory(test_id)
    print(f"Načtená metadata (po 2. přístupu): {retrieved_meta}")

    print("Test dokončen.")

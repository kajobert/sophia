import os
import uuid
import yaml
import chromadb
from sentence_transformers import SentenceTransformer
from core.rich_printer import RichPrinter

class LongTermMemory:
    """
    Spravuje dlouhodobou, sémanticky prohledávatelnou paměť agenta
    pomocí vektorové databáze ChromaDB.
    """

    def __init__(self, project_root: str = ".", db_path_override: str = None, collection_name_override: str = None):
        """
        Inicializuje klienta databáze, načte nebo vytvoří kolekci
        a připraví model pro tvorbu vektorových embeddings.
        """
        self.project_root = os.path.abspath(project_root)
        self._load_config()

        db_path = db_path_override if db_path_override else self.config.get("path", "db/chroma.db")
        self.collection_name = collection_name_override if collection_name_override else self.config.get("collection_name", "sophia_memory")

        if not os.path.isabs(db_path):
            db_path = os.path.join(self.project_root, db_path)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        try:
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            RichPrinter.info(f"LongTermMemory inicializována. Databáze: '{db_path}', Kolekce: '{self.collection_name}'")

        except Exception as e:
            RichPrinter.error(f"Kritická chyba při inicializaci ChromaDB nebo SentenceTransformer: {e}")
            raise

    def _load_config(self):
        """Načte konfiguraci z config/config.yaml."""
        config_path = os.path.join(self.project_root, "config", "config.yaml")
        try:
            with open(config_path, "r") as f:
                full_config = yaml.safe_load(f)
                self.config = full_config.get("vector_database", {})
        except FileNotFoundError:
            RichPrinter.warning("Konfigurační soubor 'config.yaml' nebyl nalezen. Používám výchozí hodnoty pro LTM.")
            self.config = {}

    def add_memory(self, text_chunk: str, metadata: dict = None):
        """
        Přidá textový záznam do dlouhodobé paměti.
        """
        if not self.collection or not self.model:
            RichPrinter.error("LTM není správně inicializována. Nelze přidat paměť.")
            return

        try:
            RichPrinter.memory_log(
                operation="WRITE",
                source="LTM (ChromaDB)",
                content={"text_chunk": text_chunk, "metadata": metadata},
            )
            embedding = self.model.encode([text_chunk])[0].tolist()
            doc_id = str(uuid.uuid4())

            safe_metadata = {}
            if metadata:
                for key, value in metadata.items():
                    safe_metadata[key] = str(value)

            add_params = {
                'ids': [doc_id],
                'embeddings': [embedding],
                'documents': [text_chunk]
            }
            if safe_metadata:
                add_params['metadatas'] = [safe_metadata]

            self.collection.add(**add_params)
        except Exception as e:
            RichPrinter.error(f"Nepodařilo se přidat záznam do ChromaDB: {e}")
            raise

    def search_memory(self, query_text: str, n_results: int = 5) -> dict:
        """
        Prohledá dlouhodobou paměť a vrátí N nejrelevantnějších záznamů.
        """
        if not self.collection or not self.model:
            RichPrinter.error("LTM není správně inicializována. Nelze prohledat paměť.")
            return {}

        if not query_text:
            return {}

        try:
            RichPrinter.memory_log(
                operation="READ",
                source="LTM (ChromaDB)",
                content={"query": query_text, "n_results": n_results},
            )
            query_embedding = self.model.encode([query_text])[0].tolist()
            count = self.collection.count()
            if count == 0:
                return {}

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, count),
                include=["metadatas", "documents"]
            )
            RichPrinter.memory_log(
                operation="READ",
                source="LTM (ChromaDB) - Result",
                content={"results_found": len(results.get("documents", [[]])[0]), "results": results},
            )
            return results
        except Exception as e:
            RichPrinter.error(f"Nepodařilo se prohledat ChromaDB: {e}")
            raise

    def clear_memory(self):
        """
        Kompletně vymaže (smaže a znovu vytvoří) aktuální kolekci.
        """
        if not self.client:
            RichPrinter.error("LTM není správně inicializována. Nelze vymazat paměť.")
            return

        try:
            RichPrinter.memory_log(
                operation="CLEAR",
                source="LTM (ChromaDB)",
                content={"collection_name": self.collection_name},
            )
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            RichPrinter.warning(f"Kolekce '{self.collection_name}' byla kompletně vymazána.")
        except Exception as e:
            RichPrinter.error(f"Nepodařilo se smazat kolekci v ChromaDB: {e}")

    def shutdown(self):
        """
        Bezpečně ukončí spojení s databází a vyčistí zdroje.
        Zásadní pro testování, aby se předešlo zamykání souborů.
        """
        # Uvolníme reference, což pomůže garbage collectoru uvolnit zámky souborů.
        # Metoda reset() je v cílovém prostředí zakázána.
        self.client = None
        self.collection = None
        RichPrinter.info("LongTermMemory shutdown.")
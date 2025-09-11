import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

class LongTermMemory:
    """
    Manages the agent's long-term (semantic) memory using ChromaDB.
    """
    def __init__(self, db_path: str = "memory/chroma_db", collection_name: str = "sophia_memories"):
        # Ujistíme se, že máme API klíč pro embedding model
        if not os.getenv("GEMINI_API_KEY"):
            raise ValueError("GEMINI_API_KEY not found in environment variables.")

        # Nastavení klienta a kolekce v ChromaDB
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        
        # Inicializace embedding modelu od Google
        self.embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    def add_memory(self, memory_text: str, metadata: dict = None):
        """
        Adds a new memory to the long-term semantic store.
        The memory text is converted into a vector embedding.
        """
        try:
            # Vytvoření embeddingu z textu
            embedding = self.embedding_model.embed_query(memory_text)
            
            # Unikátní ID pro každý záznam v paměti
            memory_id = f"mem_{self.collection.count() + 1}"

            self.collection.add(
                embeddings=[embedding],
                documents=[memory_text],
                metadatas=[metadata] if metadata else None,
                ids=[memory_id]
            )
            print(f"INFO: Memory '{memory_text[:30]}...' added to LTM with ID {memory_id}.")
        except Exception as e:
            print(f"ERROR: Failed to add memory to LTM: {e}")

    def fetch_relevant_memories(self, query_text: str, num_results: int = 3) -> list:
        """
        Fetches the most relevant memories from the LTM based on a query.
        """
        try:
            # Vytvoření embeddingu z dotazu
            query_embedding = self.embedding_model.embed_query(query_text)
            # ChromaDB očekává: query_embeddings = List[List[float]]
            # Vždy zabalíme embedding do listu (jeden dotaz = jeden embedding)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=num_results
            )
            return results.get('documents', [])
        except Exception as e:
            print(f"ERROR: Failed to fetch memories from LTM: {e}")
            return []

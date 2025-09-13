import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import numpy as np

class MockEmbeddingModel:
    """A mock embedding model for testing that returns a fixed-size vector of zeros."""
    def __init__(self, model="models/embedding-001"):
        # The real model has a dimension of 768
        self.dimension = 768

    def embed_query(self, text: str) -> list[float]:
        print(f"--- MOCK EMBEDDING: Faking embedding for text: '{text[:30]}...' ---")
        return list(np.zeros(self.dimension))

class LongTermMemory:
    """
    Manages the agent's long-term (semantic) memory using ChromaDB.
    """
    def __init__(self, db_path: str = "memory/chroma_db", collection_name: str = "sophia_memories"):
        try:
            # Nastavení klienta a kolekce v ChromaDB
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self.client.get_or_create_collection(name=collection_name)
        except Exception as e:
            print(f"WARNING: ChromaDB is missing or corrupted: {e}")
            self.client = None
            self.collection = None

        # Use mock embedding model if USE_MOCK_LLM is set
        if os.getenv("USE_MOCK_LLM") == "true":
            print("--- Using MOCK Embedding Model for testing ---")
            self.embedding_model = MockEmbeddingModel()
        else:
            # Ujistíme se, že máme API klíč pro embedding model
            if not os.getenv("GEMINI_API_KEY"):
                raise ValueError("GEMINI_API_KEY not found in environment variables.")
            # Inicializace embedding modelu od Google
            self.embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    from typing import Optional
    def add_memory(self, memory_text: str, metadata: Optional[dict] = None):
        """
        Adds a new memory to the long-term semantic store.
        The memory text is converted into a vector embedding.
        """
        if self.collection is None:
            print("WARNING: ChromaDB is not available. Memory not saved.")
            return
        try:
            # Vytvoření embeddingu z textu
            embedding = self.embedding_model.embed_query(memory_text)
            # Pokud embedding není obyčejný list, převedeme ho (např. proto.marshal.collections.repeated.Repeated)
            if not isinstance(embedding, list):
                embedding = list(embedding)
            if isinstance(embedding, list) and len(embedding) == 1 and isinstance(embedding[0], list):
                embedding = embedding[0]
            if not (isinstance(embedding, list) and all(isinstance(x, (float, int)) for x in embedding)):
                raise ValueError(f"Embedding must be a list of floats/ints, got: {type(embedding)} with sample {embedding[:5]}")
            memory_id = f"mem_{self.collection.count() + 1}"
            self.collection.add(
                embeddings=[embedding],  # ChromaDB expects List[List[float]]
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
        if self.collection is None:
            print("WARNING: ChromaDB is not available. No memories can be fetched.")
            return []
        try:
            # Vytvoření embeddingu z dotazu
            query_embedding = self.embedding_model.embed_query(query_text)
            if not isinstance(query_embedding, list):
                query_embedding = list(query_embedding)
            if isinstance(query_embedding, list) and len(query_embedding) == 1 and isinstance(query_embedding[0], list):
                query_embedding = query_embedding[0]
            if not (isinstance(query_embedding, list) and all(isinstance(x, (float, int)) for x in query_embedding)):
                raise ValueError(f"Query embedding must be a list of floats/ints, got: {type(query_embedding)} with sample {query_embedding[:5]}")
            # ChromaDB očekává: query_embeddings = List[List[float]]
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=num_results
            )
            docs = results.get('documents', [])
            if docs is None:
                return []
            return docs
        except Exception as e:
            print(f"ERROR: Failed to fetch memories from LTM: {e}")
            return []

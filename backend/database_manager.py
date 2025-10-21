import os
import datetime
import sqlalchemy
import chromadb
from chromadb.utils import embedding_functions

class DatabaseManager:
    def __init__(self, db_path='data/sophia_chat.db', chroma_path='data/chroma_db'):
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(chroma_path, exist_ok=True)

        # SQLite setup
        self.db_engine = sqlalchemy.create_engine(f'sqlite:///{db_path}')
        self.metadata = sqlalchemy.MetaData()
        self.conversations = sqlalchemy.Table(
            'conversations', self.metadata,
            sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
            sqlalchemy.Column('session_id', sqlalchemy.String, index=True),
            sqlalchemy.Column('role', sqlalchemy.String),
            sqlalchemy.Column('content', sqlalchemy.Text),
            sqlalchemy.Column('timestamp', sqlalchemy.DateTime, default=datetime.datetime.utcnow)
        )
        self.metadata.create_all(self.db_engine)

        # ChromaDB setup
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        # Using a default embedding function for simplicity.
        # A more advanced implementation might use a specific model.
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        self.memory_collection = self.chroma_client.get_or_create_collection(
            name="sophia_memory",
            embedding_function=self.embedding_function
        )

    def add_message(self, session_id: str, role: str, content: str):
        """Adds a message to the SQLite conversation history."""
        with self.db_engine.connect() as connection:
            statement = self.conversations.insert().values(
                session_id=session_id,
                role=role,
                content=content
            )
            connection.execute(statement)
            connection.commit()


    def get_recent_messages(self, session_id: str, limit: int = 10):
        """Retrieves the most recent messages for a session."""
        query = self.conversations.select().where(
            self.conversations.c.session_id == session_id
        ).order_by(self.conversations.c.timestamp.desc()).limit(limit)
        with self.db_engine.connect() as connection:
            results = connection.execute(query).fetchall()
            # Reverse the results to have them in chronological order
            return list(reversed(results))

    def add_memory(self, session_id: str, text: str, metadata: dict = None):
        """Adds a text snippet to the ChromaDB vector memory."""
        if metadata is None:
            metadata = {}
        metadata['session_id'] = session_id

        # ChromaDB needs unique IDs for each document. We can use a hash or a timestamp.
        # For simplicity, we'll use a timestamp-based unique ID.
        doc_id = f"{session_id}-{datetime.datetime.utcnow().isoformat()}"

        self.memory_collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def query_memory(self, session_id: str, query_text: str, n_results: int = 5):
        """Queries ChromaDB for relevant memories for a session."""
        results = self.memory_collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where={"session_id": session_id}
        )
        return results['documents'][0] if results['documents'] else []

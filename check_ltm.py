import chromadb

# Připojení k databázi
client = chromadb.PersistentClient(path='./memory/chroma_db')

# Získání kolekce
collection = client.get_or_create_collection(name='sophia_memories')

# Vypsání počtu položek
print(f"Počet položek v kolekci 'sophia_memories': {collection.count()}")

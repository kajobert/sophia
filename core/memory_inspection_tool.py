 
from memory.long_term_memory import LongTermMemory

def memory_inspection_tool() -> str:
    """Zobrazí veškerý obsah dlouhodobé paměti (LTM)."""
    try:
        import asyncio
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        ltm = LongTermMemory()
        all_documents = ltm.collection.get(include=['documents', 'metadatas'])
        if all_documents and all_documents.get('documents'):
            formatted_output = "Obsah dlouhodobé paměti (LTM):\n"
            for i, doc in enumerate(all_documents['documents']):
                metadata = all_documents['metadatas'][i]
                formatted_output += f"--- Dokument {i+1} ---\n"
                formatted_output += f"Obsah: {doc}\n"
                formatted_output += f"Metadata: {metadata}\n"
                formatted_output += "---------------------\n"
            return formatted_output
        else:
            return "Dlouhodobá paměť (LTM) je prázdná nebo neobsahuje žádné dokumenty."
    except Exception as e:
        return f"Chyba při inspekci dlouhodobé paměti: {e}"


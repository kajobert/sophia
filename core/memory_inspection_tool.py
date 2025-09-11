from crewai.tools import BaseTool
from memory.long_term_memory import LongTermMemory

class MemoryInspectionTool(BaseTool):
    name: str = "Memory Inspection Tool"
    description: str = "Zobrazí veškerý obsah dlouhodobé paměti (LTM)."

    def _run(self) -> str:
        try:
            # Instance LongTermMemory pro přístup k ChromaDB
            ltm = LongTermMemory()
            
            # Získání všech dokumentů z kolekce
            # Použití collection.get() bez parametrů vrátí všechny dokumenty
            all_documents = ltm.collection.get(include=['documents', 'metadatas'])
            
            if all_documents and all_documents.get('documents'):
                # Formátování výstupu pro čitelnost
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
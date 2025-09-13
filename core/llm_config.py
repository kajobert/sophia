import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Načtení proměnných prostředí ze souboru .env
load_dotenv()

# Získání API klíče z proměnných prostředí
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Kontrola, zda byl klíč nalezen
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY nebyl nalezen v .env souboru.")

# Inicializace Gemini LLM
# Model 'gemini-pro' je zde jako příklad, může být potřeba ho upravit
gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    verbose=True,
    temperature=0.7,
    google_api_key=gemini_api_key
)

# Zde můžete přidat logování nebo další konfigurace, pokud je to potřeba
print("Gemini LLM bylo úspěšně inicializováno.")

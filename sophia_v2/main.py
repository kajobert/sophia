import os
import yaml
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

def load_configuration():
    """Načte konfiguraci z .env a config.yaml."""
    load_dotenv()
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    return config

def main():
    """Hlavní funkce pro spuštění smoke testu."""
    print("🚀 Starting Sophia v2 Smoke Test...")
    config = load_configuration()
    print("✅ Configuration loaded.")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "":
        print("❌ ERROR: GEMINI_API_KEY not found or is empty in your local .env file.")
        print("👉 Please create a .env file from .env.example and add your API key.")
        return

    print("✅ Gemini API key found.")
    model_name = config.get("llm", {}).get("model_name", "gemini-1.5-flash-latest")

    try:
        llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
        print(f"✅ Initialized LLM with model: {model_name}")
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize LLM. Details: {e}")
        return

    print("\n🤙 Sending test message to Gemini...")
    try:
        response = llm.invoke("Ahoj! Stručně se představ, jsi model Gemini.")
        print("\n🎉 Gemini Response Received:")
        print("---------------------------")
        print(response.content)
        print("---------------------------")
        print("\n✅ Smoke test successful! The connection is working.")
    except Exception as e:
        print(f"❌ ERROR: API call failed. Details: {e}")

if __name__ == "__main__":
    main()

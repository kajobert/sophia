import requests
import sys

def test_backend_chat():
    try:
        resp = requests.post("http://localhost:8000/chat", json={"message": "Testuješ?"}, timeout=5)
        assert resp.status_code == 200, f"HTTP {resp.status_code}"
        data = resp.json()
        assert "reply" in data, "Chybí klíč 'reply' v odpovědi"
        print("✅ Backend /chat odpovídá správně.")
    except Exception as e:
        print(f"❌ Backend /chat není dostupný nebo odpověď není validní: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_backend_chat()

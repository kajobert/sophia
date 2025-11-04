import asyncio
import httpx

async def test_ollama():
    print("Testing Ollama directly...")
    client = httpx.AsyncClient(timeout=30)
    
    try:
        response = await client.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma2:2b",
                "prompt": "Ahoj! Jsi Sophia AI? Odpověz v češtině jednou větou.",
                "stream": False
            }
        )
        result = response.json()
        print(f"\n✅ Ollama odpověděla:\n{result.get('response', 'No response')}\n")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.aclose()

asyncio.run(test_ollama())

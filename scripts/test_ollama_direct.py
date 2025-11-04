#!/usr/bin/env python3
"""
Simple offline test without full Sophia initialization.
Just test if Ollama + Llama 3.1 8B responds.
"""

import requests
import json

print("🧪 Testing Ollama + Llama 3.1 8B directly...")

try:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.1:8b",
            "prompt": "Kolik je 2+2? Odpověz pouze číslem.",
            "stream": False
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Ollama odpověděla:")
        print(f"   {result.get('response', 'No response')}")
        print(f"\n📊 Stats:")
        print(f"   Total duration: {result.get('total_duration', 0) / 1e9:.2f}s")
        print(f"   Load duration: {result.get('load_duration', 0) / 1e9:.2f}s")
    else:
        print(f"❌ Error: HTTP {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error: {e}")

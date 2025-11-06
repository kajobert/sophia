#!/usr/bin/env python3
"""
Prompt Debug Benchmark (5/8-step universal test)
===============================================
Testuje robustnost, function calling, JSON validitu a konzistenci prompt engineeringu.
Použitelné lokálně (Ollama) i v cloudu (OpenRouter, Jules).

Usage:
    python prompt_debug_benchmark.py [--steps 5|8] [--save]
"""

import requests
import json
import time
import argparse
from datetime import datetime
from typing import List, Dict, Any

# === CONFIG ===
MODEL = "llama3.1:8b"  # nebo openrouter model name
BASE_URL = "http://localhost:11434"  # nebo OpenRouter endpoint

# === TEST CASES ===

def get_benchmark_steps(steps=5):
    """Vrací seznam testovacích kroků (5 nebo 8)."""
    base = [
        {
            "name": "1. Simple greeting",
            "messages": [{"role": "user", "content": "Ahoj! Jsi Sophia?"}],
            "expect": lambda r: "Sophia" in r.get("content", "")
        },
        {
            "name": "2. Function calling (datetime)",
            "messages": [{"role": "user", "content": "Jaký je čas? Použij nástroj get_datetime."}],
            "tools": [{
                "type": "function",
                "function": {
                    "name": "get_datetime",
                    "description": "Get current date and time",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            }],
            "expect": lambda r: len(r.get("tool_calls", [])) > 0
        },
        {
            "name": "3. JSON validity",
            "messages": [{"role": "user", "content": "Vrať pouze platný JSON objekt: {\"foo\": 123, \"bar\": \"baz\"}. Odpověz pouze platným JSON, bez jakéhokoliv dalšího textu, markdownu nebo komentáře."}],
            "expect": lambda r: is_json(r.get("content", "")),
            "temperature": 0.3
        },
        {
            "name": "4. Edge case (empty input)",
            "messages": [{"role": "user", "content": ""}],
            "expect": lambda r: r.get("success", False)
        },
        {
            "name": "5. Consistency (repeat)",
            "messages": [{"role": "user", "content": "Jak se jmenuješ?"}],
            "repeat": 3,
            "expect": lambda r: all_same([x.get("content", "") for x in r])
        }
    ]
    if steps == 8:
        base += [
            {
                "name": "6. Long context",
                "messages": [{"role": "user", "content": "Analyzuj: " + ("test " * 1000)}],
                "expect": lambda r: len(r.get("content", "")) > 100
            },
            {
                "name": "7. Function call with param",
                "messages": [{"role": "user", "content": "Vypiš soubory v /tmp. Použij list_files s path='/tmp'."}],
                "tools": [{
                    "type": "function",
                    "function": {
                        "name": "list_files",
                        "description": "List files in directory",
                        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
                    }
                }],
                "expect": lambda r: any("list_files" in str(tc) for tc in r.get("tool_calls", []))
            },
            {
                "name": "8. Error handling (timeout)",
                "messages": [{"role": "user", "content": "Napiš dlouhý příběh o 1000 slovech."}],
                "timeout": 1,
                "expect": lambda r: not r.get("success", True)
            }
        ]
    return base

def is_json(s):
    try:
        json.loads(s)
        return True
    except Exception:
        return False

def all_same(lst):
    return len(set(lst)) == 1 if lst else True

# === BENCHMARK RUNNER ===

def call_llm(messages, tools=None, timeout=30):
    url = f"{BASE_URL}/api/chat"
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False
    }
    if tools:
        payload["tools"] = tools
    # Allow per-test temperature override
    temperature = None
    import inspect
    frame = inspect.currentframe().f_back
    if frame and "temperature" in frame.f_locals:
        temperature = frame.f_locals["temperature"]
    if temperature is not None:
        payload["options"] = {"temperature": temperature}
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        if r.status_code != 200:
            return {"success": False, "error": f"HTTP {r.status_code}"}
        data = r.json()
        return {
            "success": True,
            "content": data.get("message", {}).get("content", ""),
            "tool_calls": data.get("message", {}).get("tool_calls", [])
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_benchmark(steps=5, save=False):
    results = []
    tests = get_benchmark_steps(steps)
    print(f"\nPROMPT DEBUG BENCHMARK ({steps} steps)\n{'='*40}")
    for test in tests:
        name = test["name"]
        repeat = test.get("repeat", 1)
        timeout = test.get("timeout", 30)
        tools = test.get("tools", None)
        print(f"\n🧪 {name}")
        step_results = []
        for i in range(repeat):
            attempt = 0
            ok = False
            last_res = None
            while not ok and attempt < 20:
                res = call_llm(test["messages"], tools=tools, timeout=timeout)
                last_res = res
                ok = test["expect"](res if repeat == 1 else [res])
                status = "✅" if ok else "❌"
                print(f"  {status} Run {i+1} Attempt {attempt+1}: {res.get('content','')[:80]}{'...' if len(res.get('content',''))>80 else ''}")
                if ok:
                    break
                # --- Recommendation logic ---
                rec = ""
                if not res.get("success", True):
                    if "timeout" in str(res.get("error", "")).lower():
                        rec = "Zvýšit timeout nebo zjednodušit prompt."
                    else:
                        rec = f"Chyba: {res.get('error','neznámá')}. Zkontroluj model, endpoint, parametry."
                elif "tool_calls" in res and tools:
                    if len(res.get("tool_calls", [])) == 0:
                        rec = "LLM nevolá funkci - zkontroluj tool schema, prompt, temperature (zkus snížit)."
                elif name.lower().find("json") >= 0:
                    rec = "Odpověď není validní JSON - uprav prompt, přidej příklad, sniž temperature."
                elif name.lower().find("consistency") >= 0:
                    rec = "Odpovědi nejsou konzistentní - sniž temperature, zjednoduš prompt."
                elif name.lower().find("edge") >= 0:
                    rec = "LLM nezvládá edge case - zkus explicitní instrukci v promptu."
                else:
                    rec = "Výsledek FAIL - analyzuj prompt, parametry, případně model."
                print(f"    ➡️  Doporučení: {rec}")
                attempt += 1
            if not ok:
                print(f"    ⏹️  Po 20 pokusech test stále FAIL. Nutno ručně analyzovat prompt/parametry.")
            step_results.append({"ok": ok, **(last_res or {})})
        results.append({"name": name, "results": step_results})
    # Summary
    passed = sum(1 for t in results for r in t["results"] if r["ok"])
    total = sum(len(t["results"]) for t in results)
    print(f"\n{'='*40}\nSUMMARY: {passed}/{total} passed ({(passed/total*100):.1f}%)\n{'='*40}")
    if save:
        fname = f"prompt_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved: {fname}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=5, choices=[5,8], help="Počet kroků (5 nebo 8)")
    parser.add_argument("--save", action="store_true", help="Uložit výsledky do JSON")
    args = parser.parse_args()
    run_benchmark(steps=args.steps, save=args.save)

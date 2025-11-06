#!/usr/bin/env python3
"""
Offline Mode Robustness Tuning Script
======================================
Optimalizuje a testuje lokální Llama 3.1 8B pro maximální robustnost.
Jules bude testovat přes OpenRouter samostatně.

Účel:
- Najít optimální parametry (temperature, max_tokens, timeout)
- Testovat edge cases a error handling
- Měřit kvalitu function calling
- Ověřit konzistenci výstupů

Usage:
    python tune_offline_robustness.py                # Quick test
    python tune_offline_robustness.py --full         # Full tuning suite
    python tune_offline_robustness.py --stress       # Stress tests
"""

import requests
import json
import time
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class OfflineTuner:
    """Tuning a robustness testing pro lokální Llama 3.1 8B."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "llama3.1:8b"
        self.results = []
        
    def log(self, msg: str, emoji: str = "📋"):
        """Timestamped logging."""
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {emoji} {msg}")
        
    def test_connection(self) -> bool:
        """Test Ollama connection."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if r.status_code == 200:
                self.log("Ollama connected", "✅")
                return True
        except Exception as e:
            self.log(f"Ollama connection failed: {e}", "❌")
            return False
            
    def call_ollama(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """Direct Ollama /api/chat call."""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if tools:
            payload["tools"] = tools
            
        start = time.time()
        try:
            response = requests.post(url, json=payload, timeout=timeout)
            elapsed = time.time() - start
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "elapsed": elapsed
                }
                
            data = response.json()
            return {
                "success": True,
                "message": data.get("message", {}),
                "elapsed": elapsed,
                "content": data.get("message", {}).get("content", ""),
                "tool_calls": data.get("message", {}).get("tool_calls", [])
            }
            
        except requests.Timeout:
            return {
                "success": False,
                "error": "Timeout",
                "elapsed": timeout
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed": time.time() - start
            }
            
    def test_basic_quality(self):
        """Test 1: Základní kvalita odpovědí."""
        self.log("Test 1: Základní kvalita odpovědí", "🧪")
        
        tests = [
            {
                "name": "Czech greeting",
                "messages": [{"role": "user", "content": "Ahoj! Jsi Sophia?"}],
                "check": lambda r: "Sophia" in r.get("content", "")
            },
            {
                "name": "Simple math",
                "messages": [{"role": "user", "content": "Kolik je 15 + 27? Odpověz jen číslem."}],
                "check": lambda r: "42" in r.get("content", "")
            },
            {
                "name": "Czech poem (4 verses)",
                "messages": [{"role": "user", "content": "Napiš krátkou básničku o AI (4 verše). Jen básničku, nic jiného."}],
                "check": lambda r: len(r.get("content", "").split("\n")) >= 4
            }
        ]
        
        results = []
        for test in tests:
            result = self.call_ollama(test["messages"], temperature=0.7, max_tokens=2048)
            passed = result.get("success", False) and test["check"](result)
            
            results.append({
                "test": test["name"],
                "passed": passed,
                "elapsed": result.get("elapsed", 0),
                "response": result.get("content", "")[:100]
            })
            
            status = "✅" if passed else "❌"
            self.log(f"  {status} {test['name']} ({result.get('elapsed', 0):.2f}s)", "  ")
            
        self.results.append({"category": "basic_quality", "tests": results})
        return results
        
    def test_function_calling(self):
        """Test 2: Function calling robustnost."""
        self.log("Test 2: Function calling robustnost", "🧪")
        
        # Simple datetime tool
        datetime_tool = {
            "type": "function",
            "function": {
                "name": "get_datetime",
                "description": "Get current date and time",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
        
        # File list tool with parameter
        list_tool = {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files in directory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path"}
                    },
                    "required": ["path"]
                }
            }
        }
        
        tests = [
            {
                "name": "Tool call - no params",
                "messages": [{"role": "user", "content": "Jaký je čas? Použij nástroj get_datetime."}],
                "tools": [datetime_tool],
                "check": lambda r: len(r.get("tool_calls", [])) > 0
            },
            {
                "name": "Tool call - with param",
                "messages": [{"role": "user", "content": "Vypiš soubory v /tmp. Použij list_files s path='/tmp'."}],
                "tools": [list_tool],
                "check": lambda r: any("list_files" in str(tc) for tc in r.get("tool_calls", []))
            },
            {
                "name": "No tool call needed",
                "messages": [{"role": "user", "content": "Ahoj, jak se máš?"}],
                "tools": [datetime_tool, list_tool],
                "check": lambda r: len(r.get("tool_calls", [])) == 0
            }
        ]
        
        results = []
        for test in tests:
            result = self.call_ollama(
                test["messages"],
                tools=test["tools"],
                temperature=0.3,  # Lower temp for function calling
                max_tokens=2048
            )
            passed = result.get("success", False) and test["check"](result)
            
            results.append({
                "test": test["name"],
                "passed": passed,
                "elapsed": result.get("elapsed", 0),
                "tool_calls": len(result.get("tool_calls", [])),
                "tool_names": [tc.get("function", {}).get("name", "") for tc in result.get("tool_calls", [])]
            })
            
            status = "✅" if passed else "❌"
            tc_count = len(result.get("tool_calls", []))
            self.log(f"  {status} {test['name']} ({result.get('elapsed', 0):.2f}s, {tc_count} calls)", "  ")
            
        self.results.append({"category": "function_calling", "tests": results})
        return results
        
    def test_temperature_tuning(self):
        """Test 3: Optimální temperature pro různé úkoly."""
        self.log("Test 3: Temperature tuning", "🧪")
        
        prompt = "Napiš jedno krátké rčení o moudrosti."
        temps = [0.3, 0.5, 0.7, 0.9]
        
        results = []
        for temp in temps:
            responses = []
            
            # 3 runs per temperature
            for _ in range(3):
                result = self.call_ollama(
                    [{"role": "user", "content": prompt}],
                    temperature=temp,
                    max_tokens=100
                )
                if result.get("success"):
                    responses.append(result.get("content", ""))
                    
            # Measure diversity (unique responses)
            unique = len(set(responses))
            avg_length = sum(len(r) for r in responses) / len(responses) if responses else 0
            
            results.append({
                "temperature": temp,
                "unique_responses": unique,
                "total_responses": len(responses),
                "diversity": unique / len(responses) if responses else 0,
                "avg_length": int(avg_length)
            })
            
            self.log(f"  T={temp}: {unique}/3 unique, avg {int(avg_length)} chars", "  ")
            
        self.results.append({"category": "temperature_tuning", "tests": results})
        return results
        
    def test_max_tokens_impact(self):
        """Test 4: Vliv max_tokens na kvalitu."""
        self.log("Test 4: Max tokens impact", "🧪")
        
        prompt = "Napiš podrobný popis umělé inteligence (minimálně 5 vět)."
        token_limits = [256, 512, 1024, 2048]
        
        results = []
        for max_tok in token_limits:
            result = self.call_ollama(
                [{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=max_tok,
                timeout=60
            )
            
            content = result.get("content", "")
            sentence_count = content.count(". ") + content.count("? ") + content.count("! ")
            complete = sentence_count >= 5
            
            results.append({
                "max_tokens": max_tok,
                "elapsed": result.get("elapsed", 0),
                "response_length": len(content),
                "sentences": sentence_count,
                "complete": complete
            })
            
            status = "✅" if complete else "⚠️"
            self.log(f"  {status} {max_tok} tokens: {len(content)} chars, {sentence_count} sent ({result.get('elapsed', 0):.2f}s)", "  ")
            
        self.results.append({"category": "max_tokens", "tests": results})
        return results
        
    def test_error_recovery(self):
        """Test 5: Error handling a recovery."""
        self.log("Test 5: Error handling", "🧪")
        
        tests = [
            {
                "name": "Timeout test (1s limit)",
                "messages": [{"role": "user", "content": "Napiš dlouhý příběh o 1000 slovech."}],
                "timeout": 1,
                "expect_error": True
            },
            {
                "name": "Empty message",
                "messages": [{"role": "user", "content": ""}],
                "timeout": 30,
                "expect_error": False  # Should handle gracefully
            },
            {
                "name": "Very long context",
                "messages": [{"role": "user", "content": "Analyzuj: " + ("test " * 1000)}],
                "timeout": 60,
                "expect_error": False
            }
        ]
        
        results = []
        for test in tests:
            result = self.call_ollama(
                test["messages"],
                timeout=test.get("timeout", 30),
                max_tokens=512
            )
            
            has_error = not result.get("success", False)
            passed = has_error == test["expect_error"]
            
            results.append({
                "test": test["name"],
                "passed": passed,
                "has_error": has_error,
                "expected_error": test["expect_error"],
                "error": result.get("error", "none")
            })
            
            status = "✅" if passed else "❌"
            self.log(f"  {status} {test['name']}: {result.get('error', 'OK')}", "  ")
            
        self.results.append({"category": "error_recovery", "tests": results})
        return results
        
    def print_summary(self):
        """Print comprehensive summary."""
        self.log("\n" + "="*70, "")
        self.log("TUNING SUMMARY", "📊")
        self.log("="*70, "")
        
        for category in self.results:
            cat_name = category["category"]
            tests = category["tests"]
            
            if isinstance(tests, list) and len(tests) > 0:
                if "passed" in tests[0]:
                    passed = sum(1 for t in tests if t.get("passed", False))
                    total = len(tests)
                    self.log(f"\n{cat_name}: {passed}/{total} passed", "✅" if passed == total else "⚠️")
                    
        # Recommendations
        self.log("\n" + "="*70, "")
        self.log("DOPORUČENÍ PRO OPTIMALIZACI", "💡")
        self.log("="*70, "")
        
        # Temperature recommendation
        temp_results = next((r for r in self.results if r["category"] == "temperature_tuning"), None)
        if temp_results:
            best_temp = max(temp_results["tests"], key=lambda x: x["diversity"])
            self.log(f"Optimální temperature: {best_temp['temperature']} (nejvyšší diversita)", "🎯")
            
        # Max tokens recommendation  
        token_results = next((r for r in self.results if r["category"] == "max_tokens"), None)
        if token_results:
            complete = [t for t in token_results["tests"] if t["complete"]]
            if complete:
                min_tokens = min(t["max_tokens"] for t in complete)
                self.log(f"Minimální max_tokens: {min_tokens} (pro kompletní odpovědi)", "🎯")
                
        self.log("\n" + "="*70, "")
        
    def save_results(self, filepath: str = "tuning_results.json"):
        """Save results to JSON."""
        output = {
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "base_url": self.base_url,
            "results": self.results
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
            
        self.log(f"Results saved: {filepath}", "💾")


def main():
    parser = argparse.ArgumentParser(description="Tune offline mode for robustness")
    parser.add_argument("--full", action="store_true", help="Run full test suite")
    parser.add_argument("--stress", action="store_true", help="Run stress tests")
    parser.add_argument("--save", action="store_true", help="Save results to JSON")
    args = parser.parse_args()
    
    tuner = OfflineTuner()
    
    tuner.log("OFFLINE MODE ROBUSTNESS TUNING", "🚀")
    tuner.log(f"Model: {tuner.model} @ {tuner.base_url}", "📋")
    tuner.log("="*70, "")
    
    # Check connection
    if not tuner.test_connection():
        print("\n❌ Ollama není dostupný. Spusť: ollama serve")
        return 1
        
    print()
    
    # Run tests
    try:
        tuner.test_basic_quality()
        print()
        
        tuner.test_function_calling()
        print()
        
        if args.full or args.stress:
            tuner.test_temperature_tuning()
            print()
            
            tuner.test_max_tokens_impact()
            print()
            
        tuner.test_error_recovery()
        print()
        
        tuner.print_summary()
        
        if args.save:
            tuner.save_results()
            
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Tuning přerušen")
        return 130
    except Exception as e:
        print(f"\n\n❌ Chyba: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

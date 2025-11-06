#!/usr/bin/env python3
"""
Offline Mode Tuning & Robustness Benchmark for Local Llama 3.1 8B
==================================================================
Tests and tunes offline mode for MAXIMUM robustness with local LLM.
NOT for Jules API testing (Jules will use OpenRouter separately).

This script helps optimize:
- Function calling reliability
- Response quality and consistency
- Error handling and recovery
- Edge case resilience
- Performance baselines

Usage:
    python benchmark_offline_mode.py              # Standard benchmark
    python benchmark_offline_mode.py --verbose    # Detailed output
    python benchmark_offline_mode.py --stress     # Stress tests
    python benchmark_offline_mode.py --save       # Save results JSON
"""

import sys
import time
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from plugins.tool_local_llm import LocalLLMTool
from types import SimpleNamespace


class OfflineBenchmark:
    """Benchmark suite for offline mode testing."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[Dict[str, Any]] = []
        
        # Initialize tool
        config = SimpleNamespace(
            base_url="http://localhost:11434",
            model="llama3.1:8b",
            max_tokens=131072,
            timeout=300,
            temperature=0.7
        )
        self.tool = LocalLLMTool()
        self.tool.setup(config, offline_mode=True)
        
    def log(self, msg: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "TEST": "🧪",
            "PERF": "⚡"
        }.get(level, "📋")
        print(f"[{timestamp}] {prefix} {msg}")
        
    def run_test(self, name: str, messages: List[Dict], tools: List[Dict] = None, 
                 expected_contains: str = None, expect_tool_call: bool = False) -> Dict[str, Any]:
        """Run a single test case."""
        self.log(f"Running: {name}", "TEST")
        
        start_time = time.time()
        try:
            response = self.tool.execute(
                messages=messages,
                tools=tools,
                tool_choice="auto" if tools else None
            )
            elapsed = time.time() - start_time
            
            # Extract response content
            if hasattr(response, 'content'):
                content = response.content
            elif hasattr(response, 'message') and hasattr(response.message, 'content'):
                content = response.message.content
            else:
                content = str(response)
            
            # Check for tool calls
            has_tool_calls = False
            tool_calls = []
            if hasattr(response, 'tool_calls') and response.tool_calls:
                has_tool_calls = True
                tool_calls = [
                    {
                        "name": tc.function.name if hasattr(tc.function, 'name') else str(tc.function),
                        "arguments": tc.function.arguments if hasattr(tc.function, 'arguments') else {}
                    }
                    for tc in response.tool_calls
                ]
            
            # Validate expectations
            passed = True
            errors = []
            
            if expected_contains and expected_contains not in content:
                passed = False
                errors.append(f"Expected '{expected_contains}' not found in response")
                
            if expect_tool_call and not has_tool_calls:
                passed = False
                errors.append("Expected tool call but none found")
                
            if not expect_tool_call and has_tool_calls:
                passed = False
                errors.append("Unexpected tool call found")
            
            result = {
                "name": name,
                "passed": passed,
                "elapsed_seconds": round(elapsed, 2),
                "response_length": len(content),
                "has_tool_calls": has_tool_calls,
                "tool_calls": tool_calls,
                "errors": errors,
                "response_preview": content[:200] + "..." if len(content) > 200 else content
            }
            
            if passed:
                self.log(f"PASS: {name} ({elapsed:.2f}s)", "SUCCESS")
            else:
                self.log(f"FAIL: {name} - {', '.join(errors)}", "ERROR")
                
            if self.verbose:
                self.log(f"Response: {content[:500]}", "INFO")
                if tool_calls:
                    self.log(f"Tool calls: {json.dumps(tool_calls, indent=2)}", "INFO")
                    
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            self.log(f"ERROR: {name} - {str(e)}", "ERROR")
            return {
                "name": name,
                "passed": False,
                "elapsed_seconds": round(elapsed, 2),
                "errors": [str(e)],
                "exception": type(e).__name__
            }
    
    def run_all_tests(self):
        """Run complete benchmark suite."""
        self.log("Starting Offline Mode Benchmark Suite", "INFO")
        self.log(f"Model: llama3.1:8b @ http://localhost:11434", "INFO")
        self.log("=" * 80, "INFO")
        
        # Test 1: Simple greeting (quality check)
        self.results.append(self.run_test(
            name="1. Simple Greeting",
            messages=[{"role": "user", "content": "Ahoj!"}],
            expected_contains="Sophia"
        ))
        
        # Test 2: Czech language response
        self.results.append(self.run_test(
            name="2. Czech Language",
            messages=[{"role": "user", "content": "Jak se máš? Odpověz česky."}]
        ))
        
        # Test 3: Creative task (quality + length)
        self.results.append(self.run_test(
            name="3. Creative Writing",
            messages=[{"role": "user", "content": "Napiš krátkou básničku o umělé inteligenci (4 verše)."}]
        ))
        
        # Test 4: Logical reasoning
        self.results.append(self.run_test(
            name="4. Logical Reasoning",
            messages=[{"role": "user", "content": "Pokud je dnes pondělí, jaký den bude za 100 dní?"}]
        ))
        
        # Test 5: Function calling - datetime tool
        datetime_tool = {
            "type": "function",
            "function": {
                "name": "get_current_time",
                "description": "Get current date and time",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
        self.results.append(self.run_test(
            name="5. Function Call - DateTime",
            messages=[{"role": "user", "content": "Jaký je dnes datum a čas? Použij nástroj."}],
            tools=[datetime_tool],
            expect_tool_call=True
        ))
        
        # Test 6: Function calling - file system
        list_files_tool = {
            "type": "function",
            "function": {
                "name": "list_directory",
                "description": "List files in a directory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path"}
                    },
                    "required": ["path"]
                }
            }
        }
        self.results.append(self.run_test(
            name="6. Function Call - File System",
            messages=[{"role": "user", "content": "Vypiš soubory v aktuálním adresáři. Použij nástroj list_directory s parametrem path='.'"}],
            tools=[list_files_tool],
            expect_tool_call=True
        ))
        
        # Test 7: Multi-turn conversation
        self.results.append(self.run_test(
            name="7. Multi-turn Conversation",
            messages=[
                {"role": "user", "content": "Jmenuji se Robert."},
                {"role": "assistant", "content": "Dobrý den, Roberte! Těší mě."},
                {"role": "user", "content": "Jak se jmenuji?"}
            ],
            expected_contains="Robert"
        ))
        
        # Test 8: Performance - rapid response
        self.results.append(self.run_test(
            name="8. Performance - Quick Response",
            messages=[{"role": "user", "content": "Odpověz jen 'OK'."}],
            expected_contains="OK"
        ))
        
        # Test 9: Edge case - empty tools array
        self.results.append(self.run_test(
            name="9. Edge Case - Empty Tools",
            messages=[{"role": "user", "content": "Ahoj"}],
            tools=[],
            expect_tool_call=False
        ))
        
        # Test 10: Stress test - long context
        long_prompt = "Analyzuj tento kód a vypiš hlavní funkce:\n\n" + ("def func():\n    pass\n" * 20)
        self.results.append(self.run_test(
            name="10. Stress Test - Long Context",
            messages=[{"role": "user", "content": long_prompt}]
        ))
        
        self.log("=" * 80, "INFO")
        self.print_summary()
        
    def print_summary(self):
        """Print benchmark summary."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get("passed", False))
        failed = total - passed
        
        total_time = sum(r.get("elapsed_seconds", 0) for r in self.results)
        avg_time = total_time / total if total > 0 else 0
        
        tool_call_tests = [r for r in self.results if r.get("has_tool_calls", False)]
        
        self.log("\n📊 BENCHMARK SUMMARY", "INFO")
        self.log("=" * 80, "INFO")
        self.log(f"Total Tests: {total}", "INFO")
        self.log(f"Passed: {passed} ✅", "SUCCESS" if passed == total else "INFO")
        self.log(f"Failed: {failed} ❌", "ERROR" if failed > 0 else "INFO")
        self.log(f"Success Rate: {(passed/total*100):.1f}%", "INFO")
        self.log(f"Total Time: {total_time:.2f}s", "PERF")
        self.log(f"Average Time: {avg_time:.2f}s/test", "PERF")
        self.log(f"Function Calls: {len(tool_call_tests)} tests used tools", "INFO")
        
        if failed > 0:
            self.log("\n❌ FAILED TESTS:", "ERROR")
            for r in self.results:
                if not r.get("passed", False):
                    self.log(f"  - {r['name']}: {', '.join(r.get('errors', []))}", "ERROR")
        
        # Performance metrics
        fastest = min(self.results, key=lambda r: r.get("elapsed_seconds", float('inf')))
        slowest = max(self.results, key=lambda r: r.get("elapsed_seconds", 0))
        
        self.log(f"\n⚡ PERFORMANCE:", "PERF")
        self.log(f"  Fastest: {fastest['name']} ({fastest['elapsed_seconds']}s)", "PERF")
        self.log(f"  Slowest: {slowest['name']} ({slowest['elapsed_seconds']}s)", "PERF")
        
        # Jules API readiness
        self.log("\n🔌 JULES API READINESS:", "INFO")
        if passed == total:
            self.log("  ✅ All tests passed - READY for Jules API integration", "SUCCESS")
        elif passed >= total * 0.8:
            self.log("  ⚠️ Most tests passed - Review failures before Jules API", "INFO")
        else:
            self.log("  ❌ Multiple failures - FIX before Jules API integration", "ERROR")
            
    def save_results(self, filepath: str = None):
        """Save results to JSON file."""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"benchmark_results_{timestamp}.json"
            
        output = {
            "timestamp": datetime.now().isoformat(),
            "model": "llama3.1:8b",
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.get("passed", False)),
            "total_time_seconds": sum(r.get("elapsed_seconds", 0) for r in self.results),
            "results": self.results
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
            
        self.log(f"Results saved to: {filepath}", "SUCCESS")


def main():
    parser = argparse.ArgumentParser(description="Benchmark offline mode for Jules API integration")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--save-results", "-s", action="store_true", help="Save results to JSON file")
    args = parser.parse_args()
    
    benchmark = OfflineBenchmark(verbose=args.verbose)
    
    try:
        benchmark.run_all_tests()
        
        if args.save_results:
            benchmark.save_results()
            
        # Exit code based on results
        passed = sum(1 for r in benchmark.results if r.get("passed", False))
        total = len(benchmark.results)
        
        if passed == total:
            sys.exit(0)  # All passed
        elif passed >= total * 0.8:
            sys.exit(1)  # Most passed
        else:
            sys.exit(2)  # Multiple failures
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Benchmark interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Benchmark failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()

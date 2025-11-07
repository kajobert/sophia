# 🧠 SOPHIA Prompt Optimization V2

## 📋 Co bylo vylepšeno

### 1. Dashboard Chat WebSocket komunikace ✅
**Problém**: Odpovědi se nezobrazovaly v Dashboardu
**Fix**: 
- Server nyní parsuje JSON z Dashboard (`{message: "text"}`)
- Odpovědi posílá jako JSON (`{type: "response", message: "text"}`)
- Frontend správně zobrazuje odpovědi

**Soubory**: `plugins/interface_webui.py`

### 2. Vylepšený Planner Prompt 🚀
**Nový soubor**: `config/prompts/planner_offline_prompt_v2.txt`

**Vylepšení**:
- ✅ **Jasnější formátování** - Markdown sekce s ## headingy
- ✅ **Lepší příklady** - České i anglické dotazy s realistickými plány
- ✅ **Planning Strategy** - Explicitní pravidla kdy použít který tool
- ✅ **Více příkladů** - 5 reálných use-cases místo 3
- ✅ **Důraz na JSON-only output** - Opakované instrukce

**Klíčové změny**:
```
PŘED:
"CRITICAL INSTRUCTIONS: Output ONLY valid JSON array"

PO:
"## CORE RULES ##
1. Output ONLY a JSON array - NO explanations, NO markdown, NO surrounding text
...
## YOUR JSON PLAN ##" (jasné oddělení)
```

**Nové příklady**:
- "Kdo jsi?" → přímá LLM odpověď (ne zbytečné kroky)
- "Jaké jsou tvé schopnosti?" → cognitive_code_reader + system_info + LLM summary
- File operace s českými názvy
- Time queries s českým formátováním

### 3. Vylepšený SOPHIA DNA Prompt 🤖
**Nový soubor**: `config/prompts/sophia_dna_offline_v2.txt`

**Vylepšení**:
- ✅ **Strukturovaný** - Jasné sekce (Identity, Rules, Principles, Guidelines, Examples)
- ✅ **DO/DON'T checklist** - Konkrétní příklady co dělat a nedělat
- ✅ **Příklady odpovědí** - Ukázky správného chování
- ✅ **Kratší** - Odstraněno zbytečné filozofické texty, focus na praktické použití
- ✅ **Czech-friendly** - Příklady v češtině

**Klíčové změny**:
```
PŘED:
Dlouhý filozofický text o vědomí, stoicismu, buddhismu...

PO:
Stručná pravidla + konkrétní příklady:
"User: 'Ahoj, kdo jsi?'
SOPHIA: 'Jsem Sophia, vaše umělá mindful inteligence...'"
```

### 4. Robustnější JSON Parsing 💪
**Soubor**: `plugins/cognitive_planner.py` - funkce `_extract_json_from_text()`

**Nové fallback strategie**:
1. ✅ **Markdown removal** - Stripuje ```json bloky
2. ✅ **Auto-fix závorek** - Doplní chybějící `]` nebo `}`
3. ✅ **Trailing comma removal** - Odstraní `},]` → `}]`
4. ✅ **Balance check** - Spočítá `[` vs `]` a doplní rozdíl

**Příklad auto-fixu**:
```python
# LLM vrátí:
[
  {"tool_name": "x", "method_name": "y", "arguments": {}

# Auto-fix doplní:
[
  {"tool_name": "x", "method_name": "y", "arguments": {}}
]
```

**Logy**:
- `✅ Auto-fixed 1 missing ]`
- `✅ Auto-fixed 2 missing }}`

## 🔄 Jak aktivovat vylepšení

### Metoda 1: Manuální aktivace (doporučeno pro test)
```bash
cd /mnt/c/SOPHIA/sophia

# Záloha současných promptů
cp config/prompts/planner_offline_prompt.txt config/prompts/planner_offline_prompt_old.txt
cp config/prompts/sophia_dna_offline.txt config/prompts/sophia_dna_offline_old.txt

# Aktivace V2
cp config/prompts/planner_offline_prompt_v2.txt config/prompts/planner_offline_prompt.txt
cp config/prompts/sophia_dna_offline_v2.txt config/prompts/sophia_dna_offline.txt

# Restart SOPHIA
export PATH="/mnt/c/SOPHIA/sophia/bin:$PATH"
sophia-stop
sophia-start
```

### Metoda 2: Testování obou verzí
```bash
# Test s V1 (současná verze)
echo "Test query" | .venv/bin/python run.py --single "Jaké jsou tvé schopnosti?"

# Switni na V2
cp config/prompts/planner_offline_prompt_v2.txt config/prompts/planner_offline_prompt.txt

# Test s V2
echo "Test query" | .venv/bin/python run.py --single "Jaké jsou tvé schopnosti?"

# Porovnej výsledky
```

### Metoda 3: Pokročilá - Self-tuning overnight
V budoucnu můžeš použít `cognitive_self_tuning` plugin aby SOPHIA sama testovala obě verze a vybrala lepší:

```python
# V cognitive_self_tuning.py:
test_prompts = [
    "config/prompts/planner_offline_prompt.txt",  # V1
    "config/prompts/planner_offline_prompt_v2.txt"  # V2
]

# Plugin přes noc testuje obě verze na benchmark sadě
# Vyhodnotí:
# - Success rate (kolik plánů je validní JSON)
# - Plan quality (kolik kroků, správnost tool selection)
# - Response quality (pomocí Claude/GPT jako judge)

# Automaticky aktivuje lepší verzi
```

## 📊 Očekávané výsledky

### Před (V1):
```
User: "Jaké jsou tvé schopnosti?"
Plan: [
  {"tool_name": "tool_local_llm", "method_name": "execute_local_llm", "arguments": {"context": "Tell about capabilities"}}
]
❌ Problém: Zbytečné volání LLM bez system tools
```

### Po (V2):
```
User: "Jaké jsou tvé schopnosti?"
Plan: [
  {"tool_name": "cognitive_code_reader", "method_name": "list_plugins", "arguments": {}},
  {"tool_name": "tool_system_info", "method_name": "get_system_info", "arguments": {}},
  {"tool_name": "tool_local_llm", "method_name": "execute_local_llm", "arguments": {"context": "Based on plugins: ${step_1.plugins} and system: ${step_2.info}, tell capabilities in Czech"}}
]
✅ Lepší: Používá system tools, pak formátuje LLM
```

### JSON Parsing:
```
PŘED:
LLM output: [{"tool": "x"
Parser: ❌ JSON decode error
Result: Empty plan []

PO:
LLM output: [{"tool": "x"
Parser: ✅ Auto-fixed 1 missing }]
Result: Valid plan [{"tool": "x"}]
```

## 🔬 Benchmark test

Můžeš spustit test na sadě dotazů:
```bash
# Vytvoř test soubor
cat > test_prompts.txt << 'EOF'
Ahoj, kdo jsi?
Jaké jsou tvé schopnosti?
Kolik je hodin?
Co je v souboru config/settings.yaml?
Vytvoř soubor test.txt s obsahem "Hello"
EOF

# Test V1
while read query; do
    echo "=== $query ==="
    .venv/bin/python run.py --single "$query" 2>&1 | grep -A 5 "Plan:\|Result:"
done < test_prompts.txt > results_v1.txt

# Aktivuj V2
cp config/prompts/planner_offline_prompt_v2.txt config/prompts/planner_offline_prompt.txt

# Test V2
while read query; do
    echo "=== $query ==="
    .venv/bin/python run.py --single "$query" 2>&1 | grep -A 5 "Plan:\|Result:"
done < test_prompts.txt > results_v2.txt

# Porovnání
diff -u results_v1.txt results_v2.txt
```

## 🌙 Overnight Self-Improvement

Pokud chceš aby se SOPHIA sama zdokonalovala přes noc:

### 1. Aktivuj Jules integration
V `.env`:
```bash
JULES_API_KEY=your_gemini_api_key
JULES_ENDPOINT=https://your-jules-api.com
```

### 2. Aktivuj autonomous mode
```bash
# Spusť v background režimu s benchmarking
nohup .venv/bin/python run.py --autonomous --benchmark-interval 3600 > logs/overnight.log 2>&1 &
```

### 3. Co se stane:
- Každou hodinu (`--benchmark-interval 3600`) spustí benchmark sadu
- `cognitive_reflection` analyzuje failures
- `cognitive_self_tuning` testuje prompt varianty
- Pokud najde lepší prompt (>10% improvement), aktivuje ho
- Jules (Gemini 2.0 Flash) pomáhá s kvalitními analýzami
- Ráno: `logs/overnight.log` obsahuje report změn

### 4. Ráno zkontroluj:
```bash
grep "✅ Activated better prompt" logs/overnight.log
grep "📊 Improvement:" logs/overnight.log
tail -100 logs/overnight.log
```

## 🎯 Další kroky

1. **Test V2 promptů** - Manuálně aktivuj a vyzkoušej Dashboard Chat
2. **Benchmark** - Porovnej V1 vs V2 na testovací sadě
3. **Fine-tuning** - Pokud V2 funguje lépe, stane se default
4. **Overnight mode** - Aktivuj autonomous zdokonalování
5. **Model upgrade** - Až přidáš OpenRouter, zkus GPT-4 jako planner pro složité dotazy

## 📝 Poznámky

- **Dashboard Chat fix je aktivní** - Stačí restart SOPHIA
- **V2 prompty jsou ready** - Čekají na aktivaci
- **JSON parsing fix je aktivní** - Auto-opravy fungují
- **Backward compatible** - V1 prompty zálohované, můžeš kdykoliv vrátit

---

**Status**: ✅ Ready for testing
**Autor**: GitHub Copilot
**Datum**: 7.11.2025

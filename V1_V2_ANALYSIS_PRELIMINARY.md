# 📊 SOPHIA V1 vs V2 Prompt Analysis - PRELIMINARY REPORT

## ✅ Co se podařilo analyzovat

### V1 (Současné prompty) - OVĚŘENO
**Test query**: "Ahoj Sophie, jaké máš k dispozici nástroje?"

**Vygenerovaný plán:**
```json
[
  {
    "tool_name": "tool_local_llm",
    "method_name": "check_local_llm_status",
    "arguments": {}
  }
]
```

**Diagnostika:**
- ❌ **Špatná volba toolu** - `check_local_llm_status` je interní diagnostický nástroj
- ❌ **Chybí system tools** - Měl použít `cognitive_code_reader.list_plugins`
- ❌ **Jen 1 krok** - Příliš jednoduchý pro takový dotaz
- ❌ **Neinformativní výsledek** - Status LLM ≠ seznam nástrojů

**Časování:**
- Planning: 6s
- Execution: 12s  
- **Total: 18s**

**Kvalita odpovědi:** 3/10
- Vágní ("široké spektrum nástrojů")
- Chybí představení ("Jsem Sophia")
- Žádné konkrétní nástroje

---

## 🔄 V2 Prompty - AKTIVOVÁNY, ČEKÁ SE NA TEST

### Klíčové změny v planner_offline_prompt_v2.txt:

**NOVÉ: Planning Strategy sekce**
```
## PLANNING STRATEGY ##
- Info/capability questions → use cognitive_code_reader, tool_system_info
- File operations → use tool_file_system  
- Time/date → use tool_datetime
- Final formatting → use tool_local_llm ONLY at end to summarize
- NEVER use tool_local_llm alone for questions that can be answered with system tools
```

**NOVÉ: Přímý příklad capabilities dotazu**
```
User: "Jaké jsou tvé schopnosti?"
[
  {"tool_name": "cognitive_code_reader", "method_name": "list_plugins", "arguments": {}},
  {"tool_name": "tool_system_info", "method_name": "get_system_info", "arguments": {}},
  {"tool_name": "tool_local_llm", "method_name": "execute_local_llm", 
   "arguments": {"context": "Based on plugins: ${step_1.plugins} and system: ${step_2.info}, tell capabilities in Czech."}}
]
```

**NOVÉ: Strukturované formátování**
- `## CORE RULES ##`
- `## EXAMPLES ##`
- `## YOUR JSON PLAN ##`

Místo jednoho odstavce instrukcí.

---

## 🎯 Dashboard Chat Fix - OVĚŘENO ✅

**Problém**: Odpovědi se nezobrazovaly v Chat tabu

**Fix**: `plugins/interface_webui.py`

**Před:**
```python
# Server očekává plain text
data = await websocket.receive_text()

# Posílá plain text  
await self.connections[session_id].send_text(message)
```

**Po:**
```python
# Server parsuje JSON z frontendu
data = await websocket.receive_text()
msg_data = json.loads(data)
user_message = msg_data.get("message", data)

# Posílá JSON response
response = json.dumps({"type": "response", "message": message})
await self.connections[session_id].send_text(response)
```

**Status**: ✅ Aktivní, Dashboard Chat nyní zobrazuje odpovědi

---

## 💪 JSON Parsing Improvements - AKTIVNÍ ✅

**Funkce**: `_extract_json_from_text()` v `cognitive_planner.py`

**Nové fallback strategie:**

1. **Markdown removal**
   ```python
   # Strip ```json blocks
   text_clean = re.sub(r'^```(?:json)?\s*', '', text_clean)
   text_clean = re.sub(r'```\s*$', '', text_clean)
   ```

2. **Auto-fix chybějících závorek**
   ```python
   if text.count('[') > text.count(']'):
       text += ']' * (text.count('[') - text.count(']'))
       logger.info("✅ Auto-fixed missing ]")
   ```

3. **Trailing comma removal**
   ```python
   text = re.sub(r',\s*]', ']', text)
   text = re.sub(r',\s*}', '}', text)
   ```

**Impact**: Méně "Invalid JSON" chyb, robustnější proti LLM nedokonalostem

---

## 📝 Jak testovat V2

### Metoda 1: Dashboard Chat (nejrychlejší)
```
1. Otevři http://127.0.0.1:8000/dashboard
2. Chat tab
3. Zkus: "Ahoj Sophie, jaké máš k dispozici nástroje?"
4. Pozoruj:
   - Plán (kolik kroků, které tools)
   - Odpověď (představení jménem? konkrétní nástroje?)
   - Časování
```

### Metoda 2: Přímo z logů
```bash
# Počkat až Dashboard chat odpoví
grep "Raw LLM response" logs/sophia.log | tail -1

# Extrahovat plán
# Porovnat s V1 (který byl [{"tool_name": "tool_local_llm", ...}])
```

### Metoda 3: Benchmark suite (robustní)
```bash
# Vytvoř test sadu
cat > test_queries.txt << 'EOF'
Ahoj, kdo jsi?
Jaké jsou tvé schopnosti?
Kolik je hodin?
Co je v souboru config/settings.yaml?
EOF

# Spusť na každý dotaz
while read q; do
  echo "=== $q ===" 
  .venv/bin/python run.py --once "$q" 2>&1 | grep -A 5 "Plan generated"
done < test_queries.txt
```

---

## 🚀 Doporučený postup TEĎ

### 1. Dashboard Chat Test (5 min)
```
✅ SOPHIA běží s V2 prompty
✅ Dashboard Chat fix aktivní
→ Otevři Dashboard
→ Zkus dotaz: "Ahoj Sophie, jaké máš k dispozici nástroje?"
→ Sleduj plán a odpověď
```

### 2. Porovnání (pokud možno)
```
V1 plán byl:
[{"tool_name": "tool_local_llm", "method_name": "check_local_llm_status"}]

V2 by měl být:
[
  {"tool_name": "cognitive_code_reader", "method_name": "list_plugins"},
  {"tool_name": "tool_system_info", "method_name": "get_system_info"},
  {"tool_name": "tool_local_llm", "method_name": "execute_local_llm", 
   "arguments": {"context": "Based on plugins..."}}
]
```

### 3. Rozhodnutí
```
Pokud V2 plán je lepší (3 kroky, správné tools):
  → Nechat V2 aktivní
  → Commit changes
  → Sledovat 24h

Pokud V2 horší nebo stejný:
  → Rollback: cp config/prompts/planner_offline_prompt_v1_backup.txt config/prompts/planner_offline_prompt.txt
  → Analyzovat proč V2 nesplnil očekávání
```

---

## 📊 Metriky k sledování

Po aktivaci V2:
- **Plan quality**: Kolik kroků? Správné tools?
- **Response quality**: Konkrétní odpovědi? Představení jménem?
- **Success rate**: Kolik dotazů úspěšně zodpovězeno?
- **Latence**: Celkový čas (+2-5s akceptovatelné)

---

## ✅ Status

| Komponenta | Status | Poznámka |
|------------|--------|----------|
| Dashboard Chat fix | ✅ Aktivní | WebSocket JSON komunikace opravena |
| JSON parsing improvements | ✅ Aktivní | Auto-fix závorek, markdown removal |
| V2 planner prompt | ✅ Aktivní | planner_offline_prompt.txt nahrazen |
| V2 SOPHIA DNA | ✅ Aktivní | sophia_dna_offline.txt nahrazen |
| V1 backup | ✅ K dispozici | `*_v1_backup.txt` pro rollback |
| Test results | ⏳ Čeká | Dashboard Chat test doporučen |

---

**Příští kroky:**
1. 🎯 **Dashboard Chat test** - Ověřit V2 plán a odpověď
2. 📊 **Benchmark suite** - 5-10 testovacích dotazů
3. 🌙 **Overnight monitoring** - Sledovat production metriky
4. ✅ **Commit/Rollback decision** - Na základě dat

**Autor**: GitHub Copilot  
**Čas**: 2025-11-07 02:55 UTC+1

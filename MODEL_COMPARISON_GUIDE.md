# 🧪 Model Comparison Test Guide

## Test Query
```
"Ahoj Sophie, jaké máš k dispozici nástroje?"
```

## Tests to Run

### ✅ TEST 1: GPT-4o-mini (ONLINE) - READY NOW
**Status**: SOPHIA běží s GPT-4o-mini

**Kroky:**
1. Otevři Dashboard: http://127.0.0.1:8000/dashboard
2. Chat tab → Napiš dotaz
3. Sleduj:
   - Počet kroků v plánu
   - Které tools použil
   - Kvalita odpovědi
   - Čas (rychlost)

**Po testu:**
```bash
# Extrahuj výsledky
tail -100 logs/sophia.log | grep "Raw LLM response" | tail -1 > test_results/gpt4o_plan.txt
tail -100 logs/sophia.log | grep "Response ready" | tail -1 > test_results/gpt4o_response.txt
```

---

### TEST 2: llama3.1:8b (OFFLINE)
**Kroky:**
```bash
# 1. Zakomentuj API klíč
nano .env
# Zakomentuj: # OPENROUTER_API_KEY=...
# Nastav: SOPHIA_FORCE_LOCAL_ONLY=true

# 2. Nastav llama3.1:8b
nano config/settings.yaml
# Ujisti se: model: "llama3.1:8b"

# 3. Restart
sophia-stop && sleep 2 && sophia-start

# 4. Test v Dashboardu (stejný dotaz)

# 5. Extrahuj výsledky
tail -100 logs/sophia.log | grep "Raw LLM response" | tail -1 > test_results/llama_plan.txt
tail -100 logs/sophia.log | grep "Response ready" | tail -1 > test_results/llama_response.txt
```

---

### TEST 3: qwen2.5:14b (OFFLINE)
**Kroky:**
```bash
# 1. Ujisti se API klíč zakomentován (z TEST 2)

# 2. Změň model
nano config/settings.yaml
# Změň na: model: "qwen2.5:14b"

# 3. Restart
sophia-stop && sleep 2 && sophia-start

# 4. Test v Dashboardu

# 5. Extrahuj výsledky
tail -100 logs/sophia.log | grep "Raw LLM response" | tail -1 > test_results/qwen_plan.txt
tail -100 logs/sophia.log | grep "Response ready" | tail -1 > test_results/qwen_response.txt
```

---

## Comparison Metrics

Pro každý model zaznamenej:

1. **Plán:**
   - Počet kroků: ?
   - Použité tools: ?
   - JSON validita: ✅/❌

2. **Odpověď:**
   - Představení jménem: ✅/❌
   - Konkrétní nástroje: ✅/❌
   - Kvalita (1-10): ?

3. **Performance:**
   - Čas plánování: ?s
   - Celkový čas: ?s
   - Cena (GPT): $?

4. **Overall:**
   - Kvalita: ?/10
   - Rychlost: ?/10
   - Hodnota: ?/10

---

## Quick Analysis Script

Po všech 3 testech:

```bash
cat > analyze_results.sh << 'EOF'
#!/bin/bash
echo "# Model Comparison Results"
echo ""
echo "## GPT-4o-mini (Online)"
echo "Plan:"
python3 -c "import json; print(json.dumps(json.load(open('test_results/gpt4o_plan.txt')), indent=2))" 2>/dev/null || cat test_results/gpt4o_plan.txt
echo ""
echo "Response:"
head -c 300 test_results/gpt4o_response.txt
echo ""
echo ""

echo "## llama3.1:8b (Offline)"
echo "Plan:"
python3 -c "import json; print(json.dumps(json.load(open('test_results/llama_plan.txt')), indent=2))" 2>/dev/null || cat test_results/llama_plan.txt
echo ""
echo "Response:"
head -c 300 test_results/llama_response.txt
echo ""
echo ""

echo "## qwen2.5:14b (Offline)"
echo "Plan:"
python3 -c "import json; print(json.dumps(json.load(open('test_results/qwen_plan.txt')), indent=2))" 2>/dev/null || cat test_results/qwen_plan.txt
echo ""
echo "Response:"
head -c 300 test_results/qwen_response.txt
EOF

chmod +x analyze_results.sh
./analyze_results.sh > FINAL_COMPARISON.md
cat FINAL_COMPARISON.md
```

---

## Expected Results

### GPT-4o-mini
- ✅ Multi-step plan (3+ kroky)
- ✅ Správné tools (cognitive_code_reader, system_info)
- ✅ Vysoká kvalita
- ⚠️ Stojí peníze (~$0.0001/dotaz)
- ⚠️ Vyžaduje internet

### llama3.1:8b
- ⚠️ Single-step plan (1 krok)
- ⚠️ Suboptimální tools
- ✅ Zdarma
- ✅ Offline
- ✅ Rychlý

### qwen2.5:14b
- ? Multi-step? (doufejme lepší než llama)
- ? Tools selection
- ✅ Zdarma
- ✅ Offline
- ⚠️ Pomalejší než llama

---

## Decision Matrix

Po testech rozhodnutí:

**Pokud GPT >> qwen >> llama:**
→ Použít GPT pro planning, qwen pro execution (hybrid)

**Pokud qwen ≈ GPT >> llama:**
→ Použít qwen jako default

**Pokud GPT >>> qwen ≈ llama:**
→ Buď GPT (platit) nebo akceptovat lower quality

---

**Status:** TEST 1 (GPT-4o-mini) READY TO RUN  
**Next:** Otevři Dashboard a testuj!

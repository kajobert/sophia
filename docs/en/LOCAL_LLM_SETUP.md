# Local LLM Setup Guide

**Run LLMs locally on your Lenovo Legend for cost-free, private AI inference!**

---

## 🚀 Quick Start (Recommended: Ollama)

### 1. Install Ollama

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Windows
# Download from https://ollama.com/download
```

### 2. Download Model (Choose one)

```bash
# Gemma 2 2B (Fastest, 1.6GB)
ollama pull gemma2:2b

# Gemma 2 9B (Better quality, 5.5GB)
ollama pull gemma2:9b

# Llama 3.2 3B (Fast, good balance)
ollama pull llama3.2:3b

# Llama 3.1 8B (Better quality, 4.7GB)
ollama pull llama3.1:8b

# Mistral 7B (Great for coding)
ollama pull mistral:7b

# Phi-3 Mini (Microsoft, fast, 2.3GB)
ollama pull phi3:mini
```

### 3. Start Ollama

```bash
# Ollama runs as daemon by default
ollama serve

# Test it works:
ollama run gemma2:2b "Hello, how are you?"
```

### 4. Configure Sophia

Edit `config/settings.yaml`:

```yaml
plugins:
  tool_local_llm:
    enabled: true
    local_llm:
      runtime: "ollama"
      base_url: "http://localhost:11434"
      model: "gemma2:2b"  # Your chosen model
      timeout: 120
      max_tokens: 2048
      temperature: 0.7
```

### 5. Test with Sophia

```bash
python run.py

# In Sophia chat:
> "Use local LLM to explain async programming in Python"
```

---

## 🎯 Recommended Models for Lenovo Legend

Based on your hardware (assuming 16-32GB RAM, decent GPU):

### **Best for Speed + Cost (Recommended for dev)**
- **Gemma 2 2B** - Ultra-fast, low memory (~2GB), Google quality
- **Phi-3 Mini** - Microsoft model, great for coding tasks
- **Llama 3.2 3B** - Meta's efficient model

### **Best for Quality (if you have GPU/RAM)**
- **Llama 3.1 8B** - Excellent balance, coding-capable
- **Gemma 2 9B** - Google's mid-size powerhouse
- **Mistral 7B** - Great for technical/coding tasks

### **Best for Coding (Specialized)**
- **CodeLlama 7B** - `ollama pull codellama:7b`
- **DeepSeek Coder 6.7B** - `ollama pull deepseek-coder:6.7b`

---

## 📊 Performance Comparison

| Model | Size | RAM | Speed | Quality | Use Case |
|-------|------|-----|-------|---------|----------|
| Gemma 2 2B | 1.6GB | 4GB | ⚡⚡⚡ | ⭐⭐⭐ | Dev, testing, fast tasks |
| Llama 3.2 3B | 2GB | 6GB | ⚡⚡ | ⭐⭐⭐⭐ | General use, balanced |
| Phi-3 Mini | 2.3GB | 4GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | Coding, Microsoft style |
| Llama 3.1 8B | 4.7GB | 10GB | ⚡ | ⭐⭐⭐⭐⭐ | Production quality |
| Gemma 2 9B | 5.5GB | 12GB | ⚡ | ⭐⭐⭐⭐⭐ | High-quality tasks |
| Mistral 7B | 4.1GB | 8GB | ⚡⚡ | ⭐⭐⭐⭐ | Coding, technical |

---

## 🔧 Alternative Runtimes

### Option 2: LM Studio (GUI)

**Pros:** Easy GUI, model browser, no terminal needed  
**Cons:** Heavier than Ollama

1. Download: https://lmstudio.ai/
2. Install and launch
3. Browse and download model (Gemma 2, Llama, etc.)
4. Start local server (click "Local Server" tab)
5. Configure Sophia:

```yaml
plugins:
  tool_local_llm:
    enabled: true
    local_llm:
      runtime: "lmstudio"
      base_url: "http://localhost:1234"  # LM Studio default
      model: "gemma-2-2b-it"
```

### Option 3: llamafile (Single Binary)

**Pros:** No installation, portable, all-in-one  
**Cons:** Larger file size per model

1. Download model: https://github.com/Mozilla-Ocho/llamafile
2. Make executable:
   ```bash
   chmod +x gemma-2-2b.llamafile
   ```
3. Run:
   ```bash
   ./gemma-2-2b.llamafile --server --port 8080
   ```
4. Configure Sophia:
   ```yaml
   plugins:
     tool_local_llm:
       enabled: true
       local_llm:
         runtime: "llamafile"
         base_url: "http://localhost:8080"
         model: "gemma-2-2b"
   ```

---

## 💡 Usage Examples

### Check Local LLM Status

```python
# Sophia will use this tool automatically
"Check if local LLM is running and list available models"
```

**Response:**
```json
{
  "available": true,
  "runtime": "ollama",
  "current_model": "gemma2:2b",
  "available_models": ["gemma2:2b", "llama3.1:8b", "mistral:7b"],
  "total_models": 3
}
```

### Generate Text Locally

```python
# Sophia auto-routes simple tasks to local LLM
"Summarize this code using local model: [code here]"
```

### Manual Tool Call

```python
# If you want to force local LLM usage
"Use execute_local_llm to write a Python function that calculates fibonacci"
```

---

## 🎯 Task Routing Strategy

Configure in `config/autonomy.yaml`:

```yaml
llm_optimization:
  prefer_cheap_models: true
  use_local_when_possible: true
  
  task_routing:
    simple_tasks: "local"           # Gemma 2 2B - $0
    medium_tasks: "cheap_cloud"     # DeepSeek - $0.14/1M
    complex_tasks: "premium_cloud"  # Claude Sonnet - $3/1M
```

**Simple tasks (→ local):**
- Code formatting, linting suggestions
- Simple summarization
- Template generation
- Documentation updates

**Medium tasks (→ cheap cloud):**
- Code review
- Bug analysis
- Feature planning

**Complex tasks (→ premium cloud):**
- Architecture design
- Complex refactoring
- Multi-file changes

---

## 🔍 Troubleshooting

### "Connection refused"
```bash
# Check if Ollama is running
ollama list

# Start Ollama
ollama serve
```

### "Model not found"
```bash
# List available models
ollama list

# Download model
ollama pull gemma2:2b
```

### "Out of memory"
- Use smaller model (Gemma 2 2B, Phi-3 Mini)
- Close other applications
- Check RAM usage: `htop` or Task Manager

### "Slow response"
- Use quantized models (4-bit or 8-bit)
- Smaller models are faster
- Check CPU/GPU usage
- Consider GPU acceleration (CUDA/Metal)

---

## 📈 Performance Optimization

### GPU Acceleration (Nvidia)

```bash
# Install CUDA-enabled Ollama build
# Automatic on Linux with Nvidia GPU

# Check GPU usage
nvidia-smi
```

### CPU Optimization

```bash
# Set thread count (adjust for your CPU)
export OLLAMA_NUM_THREADS=8

# Run Ollama
ollama serve
```

### Memory Management

```yaml
# In config for smaller models
local_llm:
  model: "gemma2:2b"
  max_tokens: 1024  # Reduce for faster response
```

---

## 💰 Cost Savings

**Monthly comparison (moderate usage: ~10M tokens):**

| Scenario | Cost | Notes |
|----------|------|-------|
| GPT-4 Turbo | $100-150 | Premium cloud |
| Claude Sonnet | $30-45 | Mid-tier cloud |
| DeepSeek | $1.40 | Budget cloud |
| **Local Gemma 2** | **$0** | ✅ Electricity only |

**Annual savings: $360-1,800!**

---

## 🔐 Privacy Benefits

✅ **Data stays local** - No API calls, no data leaves your PC  
✅ **No rate limits** - Unlimited usage  
✅ **Offline capable** - Works without internet  
✅ **No API keys** - Zero configuration  
✅ **Compliance friendly** - GDPR, HIPAA, SOC2 compatible  

---

## 🎓 Learning Resources

**Ollama:**
- Docs: https://ollama.com/docs
- Models: https://ollama.com/library
- Discord: https://discord.gg/ollama

**LM Studio:**
- Website: https://lmstudio.ai/
- Docs: https://lmstudio.ai/docs

**Model Comparisons:**
- Leaderboards: https://chat.lmsys.org/
- Benchmarks: https://huggingface.co/spaces/lmsys/chatbot-arena-leaderboard

---

## 🚀 Next Steps

1. ✅ Install Ollama
2. ✅ Download Gemma 2 2B (fast setup)
3. ✅ Test with `ollama run gemma2:2b`
4. ✅ Configure Sophia
5. ✅ Start using local LLM!

**For production:**
- Experiment with different models
- Benchmark against your tasks
- Set up task routing
- Monitor performance

---

**Ready to go local! 🎉**

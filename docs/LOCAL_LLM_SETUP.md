# 🏠 Local LLM Setup Guide

**Run Sophia completely offline with local AI models!**

Zero API costs. Complete privacy. Full control.

---

## 🎯 Why Local LLMs?

- **💰 Zero Cost:** No API fees, run unlimited inference
- **🔒 Privacy:** Your data never leaves your machine
- **⚡ Speed:** No network latency for simple tasks
- **🧪 Experimentation:** Test prompts and models freely
- **🌐 Offline:** Work anywhere without internet

---

## 🚀 Quick Start (Ollama - Recommended)

### 1. Install Ollama

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama

# Windows
# Download installer from https://ollama.com
```

### 2. Download a Model

```bash
# Recommended starter model (2B params, ~1.5GB)
ollama pull gemma2:2b

# Alternative options:
ollama pull llama3.2:3b     # Meta's Llama 3.2 (3B params)
ollama pull phi3:mini       # Microsoft Phi-3 (3.8B params)
ollama pull qwen2.5:3b      # Alibaba Qwen 2.5 (3B params)
```

### 3. Configure Sophia

Edit `.env` file:

```bash
LOCAL_LLM_RUNTIME=ollama
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=gemma2:2b
```

### 4. Test It

```python
# In Python REPL or script
import asyncio
from plugins.tool_local_llm import LocalLLMTool

async def test():
    llm = LocalLLMTool()
    llm.setup({"local_llm": {
        "runtime": "ollama",
        "model": "gemma2:2b"
    }})
    
    response = await llm.generate("Hello! Introduce yourself.")
    print(response)

asyncio.run(test())
```

**Done!** 🎉 Sophia can now use local AI.

---

## 🎨 Alternative Runtimes

### LM Studio (GUI-Based)

**Best for:** Users who prefer graphical interfaces.

1. **Download:** https://lmstudio.ai
2. **Install:** Run installer for your OS
3. **Load Model:** Browse catalog, download model (e.g., Llama 3.2 3B)
4. **Start Server:** Click "Local Server" tab → Start Server
5. **Configure Sophia:**

```bash
LOCAL_LLM_RUNTIME=lmstudio
LOCAL_LLM_BASE_URL=http://localhost:1234
LOCAL_LLM_MODEL=llama-3.2-3b-instruct
```

### llamafile (Single Binary)

**Best for:** Deployment simplicity.

1. **Download:** https://github.com/Mozilla-Ocho/llamafile/releases
2. **Make Executable:** `chmod +x llamafile-*.llamafile`
3. **Run:** `./llamafile-*.llamafile --server --nobrowser`
4. **Configure Sophia:**

```bash
LOCAL_LLM_RUNTIME=llamafile
LOCAL_LLM_BASE_URL=http://localhost:8080
LOCAL_LLM_MODEL=mistral-7b
```

---

## 📊 Recommended Models

| Model | Size | RAM Needed | Speed | Quality | Use Case |
|-------|------|------------|-------|---------|----------|
| **Gemma 2 2B** | 1.5GB | 4GB | ⚡⚡⚡ | ⭐⭐⭐ | General tasks, fast responses |
| **Llama 3.2 3B** | 2GB | 6GB | ⚡⚡ | ⭐⭐⭐⭐ | Better reasoning, coding |
| **Phi-3 Mini** | 2.3GB | 8GB | ⚡⚡ | ⭐⭐⭐⭐ | Microsoft fine-tune, instruction following |
| **Qwen 2.5 7B** | 4.7GB | 12GB | ⚡ | ⭐⭐⭐⭐⭐ | Best quality, multilingual |
| **Llama 3.1 8B** | 4.9GB | 16GB | ⚡ | ⭐⭐⭐⭐⭐ | Production-grade reasoning |

**Pro Tip:** Start with **Gemma 2 2B** - excellent quality/speed ratio!

---

## ⚙️ Advanced Configuration

### Custom Settings in `.env`

```bash
# Model selection
LOCAL_LLM_MODEL=gemma2:2b

# Performance tuning
LOCAL_LLM_TIMEOUT=120          # Request timeout (seconds)
LOCAL_LLM_MAX_TOKENS=2048      # Maximum output length
LOCAL_LLM_TEMPERATURE=0.7      # Creativity (0.0 = deterministic, 1.0 = creative)

# Network settings
LOCAL_LLM_BASE_URL=http://localhost:11434
```

### Runtime-Specific Endpoints

**Ollama:**
- Default Port: `11434`
- API Format: OpenAI-compatible
- Health Check: `curl http://localhost:11434/api/tags`

**LM Studio:**
- Default Port: `1234`
- API Format: OpenAI-compatible
- UI: http://localhost:1234

**llamafile:**
- Default Port: `8080`
- API Format: OpenAI-compatible
- UI: http://localhost:8080

---

## 🐛 Troubleshooting

### Ollama: "Connection refused"

**Solution:** Start Ollama service:

```bash
ollama serve
```

### LM Studio: "Model not loaded"

**Solution:** In LM Studio UI, click "Load Model" before starting server.

### llamafile: Permission denied

**Solution:** Make file executable:

```bash
chmod +x llamafile-*.llamafile
```

### Slow responses (>30s)

**Solutions:**
1. Use smaller model (gemma2:2b instead of llama3.1:70b)
2. Reduce `LOCAL_LLM_MAX_TOKENS` to 1024
3. Check CPU/RAM usage (close other apps)
4. For Mac: Ensure running on Apple Silicon (M1/M2/M3)

### Out of memory errors

**Solution:** Use quantized models:

```bash
# 4-bit quantization (75% smaller)
ollama pull gemma2:2b-q4_K_M

# 8-bit quantization (50% smaller, better quality)
ollama pull llama3.2:3b-q8_0
```

---

## 🧪 Testing Local LLM

### Interactive Testing

```bash
# Ollama CLI
ollama run gemma2:2b
>>> Hello!
>>> /bye
```

### HTTP Testing

```bash
# Test Ollama API
curl http://localhost:11434/api/generate -d '{
  "model": "gemma2:2b",
  "prompt": "Hello! Introduce yourself.",
  "stream": false
}'
```

### Sophia Integration Test

```bash
# Single-run test with local LLM
python run.py --once "Using local AI, solve: 2+2=?"
```

---

## 📚 Additional Resources

- **Ollama Documentation:** https://github.com/ollama/ollama/blob/main/docs/api.md
- **LM Studio Docs:** https://lmstudio.ai/docs
- **llamafile Guide:** https://github.com/Mozilla-Ocho/llamafile
- **Model Leaderboards:** https://huggingface.co/spaces/lmsys/chatbot-arena-leaderboard

---

## 💡 Pro Tips

1. **Start small:** Test with gemma2:2b before trying larger models
2. **Use GPU:** If you have NVIDIA GPU, Ollama auto-detects and accelerates inference
3. **Quantization:** 4-bit models are 75% smaller with minimal quality loss
4. **Context length:** Longer prompts need more RAM - keep under 2048 tokens for 2B models
5. **Multi-model:** Keep multiple models installed for different tasks (fast vs. quality)

---

**Happy Local AI Experimentation!** 🚀🏠

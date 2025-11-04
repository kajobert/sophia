# 🤖 AI Agent Quick Reference

## Running Sophia

### Basic Commands

```bash
# Simple question (user-friendly, minimal logs)
python run.py --once "Your question here"

# Debug mode (verbose logging for development)
python run.py --debug --once "Your question here"

# Interactive mode (full conversation)
python run.py

# With specific UI style
python run.py --ui matrix  # or startrek, cyberpunk, classic
```

### Helper Scripts

```bash
# Run with live logging (recommended for agents)
./scripts/sophia_run.sh --once "Question"

# Debug mode with live logging
./scripts/sophia_run.sh --debug --once "Question"

# Watch live output in separate terminal
./scripts/sophia_watch.sh /tmp/sophia_live.log
```

## Monitoring & Debugging

### Real-time Monitoring
```bash
# Terminal 1: Run Sophia
./scripts/sophia_run.sh --debug --once "Test question"

# Terminal 2: Watch output
./scripts/sophia_watch.sh /tmp/sophia_live.log
```

### Process Management
```bash
# Check if Sophia is running
ps aux | grep "python run.py" | grep -v grep

# Kill stuck process
pkill -f "python run.py"

# Check Ollama status
ollama list
ps aux | grep ollama
```

### Log Files
- **Live log:** `/tmp/sophia_live.log` (when using sophia_run.sh)
- **Application logs:** `logs/` directory
- **Test outputs:** `/tmp/sophia_test.log`, `/tmp/llama_test.log`, etc.

## Configuration

### Environment Variables (.env)
```bash
# View current LLM model
grep LOCAL_LLM_MODEL .env

# Switch models
sed -i 's/LOCAL_LLM_MODEL=.*/LOCAL_LLM_MODEL=llama3.1:8b/' .env
```

### Settings (config/settings.yaml)
```bash
# View local LLM config
grep -A 5 "tool_local_llm:" config/settings.yaml
```

## Testing

### Quick Tests
```bash
# Test Ollama directly
ollama run llama3.1:8b "Hello, how are you?"

# Test with specific model
ollama run gemma2:2b "Test question"

# Benchmark model
python -m pytest tests/ -k benchmark
```

### Full Test Suite
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## Tips for AI Agents

### ✅ DO:
- Use `--debug` flag when debugging issues
- Use `sophia_run.sh` for live logging
- Run long operations with `timeout` or in background (`&`)
- Check process status with `ps aux` before killing
- Save outputs to files with `> file.txt 2>&1`

### ❌ DON'T:
- Don't pipe to `head` unless necessary (delays output)
- Don't rely on shell integration (not available in WSL)
- Don't use interactive prompts without timeout
- Don't forget to activate venv (scripts do it automatically)

### Background Execution Pattern
```bash
# Run in background, wait, then check results
python run.py --once "Question" > /tmp/output.log 2>&1 & 
SOPHIA_PID=$!
echo "Sophia PID: $SOPHIA_PID"
sleep 60
cat /tmp/output.log
```

## Common Issues

### Output Buffering
Python buffers stdout. Solutions:
- Use `python -u` (unbuffered)
- Use `tee` for real-time output
- Use helper scripts that handle this

### Hanging Process
```bash
# Check if still running
ps aux | grep "python run.py"

# Kill gracefully
pkill -f "python run.py"

# Force kill if needed
pkill -9 -f "python run.py"
```

### Missing Dependencies
```bash
# Reinstall from requirements
uv pip sync requirements-dev.txt

# Check environment
python -c "import sys; print(sys.executable)"
which python
```

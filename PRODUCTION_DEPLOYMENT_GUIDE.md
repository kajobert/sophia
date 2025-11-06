# SOPHIA AMI 1.0 - Production Deployment Guide

**Date:** 2025-11-06  
**Status:** ✅ Production Ready  
**Components:** Worker + Guardian Watchdog + Dashboard

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│  systemd: sophia-guardian.service                    │
│  ┌────────────────────────────────────────────────┐  │
│  │  Guardian Watchdog (Phoenix Protocol)          │  │
│  │  - Monitors worker process                     │  │
│  │  - Auto-restart on crash                       │  │
│  │  - Crash log preservation                      │  │
│  │  - Git rollback on crash loops                 │  │
│  │  ┌──────────────────────────────────────────┐  │  │
│  │  │  Worker: scripts/autonomous_main.py      │  │  │
│  │  │  - Processes tasks from queue            │  │  │
│  │  │  - Offline-only (Ollama)                 │  │  │
│  │  │  - Auto-reflection logging               │  │  │
│  │  └──────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  Dashboard (Optional - Monitoring Only)              │
│  scripts/dashboard_server.py → http://localhost:8000│
└──────────────────────────────────────────────────────┘
```

---

## Prerequisites

1. **System:** Linux with systemd (Ubuntu/Debian recommended)
2. **User:** `sophia` user with home directory `/home/sophia/sophia`
3. **Python:** Python 3.10+ with virtualenv at `.venv/`
4. **Ollama:** Running with `llama3.1:8b` model
5. **Permissions:** User must have write access to logs/, sandbox/, .data/

---

## Installation Steps

### 1. Prepare Environment

```bash
# Clone repository
cd /home/sophia
git clone <repo-url> sophia
cd sophia

# Create virtualenv and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Initialize directories
mkdir -p logs sandbox .data data/chroma_db data/memory

# Configure environment
cp config/local_llm.example.yaml config/local_llm.yaml
# Edit config/local_llm.yaml to match your Ollama setup
```

### 2. Install Guardian Service (RECOMMENDED)

This runs the worker under Guardian supervision (auto-restart, crash recovery).

```bash
# Copy systemd unit file
sudo cp sophia-guardian.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable sophia-guardian.service

# Start service
sudo systemctl start sophia-guardian.service

# Check status
sudo systemctl status sophia-guardian.service
```

### 3. Alternative: Install Worker Service (Without Guardian)

If you prefer systemd-only restart (no crash logging, no git rollback):

```bash
# Copy systemd unit file
sudo cp sophia-ami.service /etc/systemd/system/

# Reload, enable, start
sudo systemctl daemon-reload
sudo systemctl enable sophia-ami.service
sudo systemctl start sophia-ami.service

# Check status
sudo systemctl status sophia-ami.service
```

**NOTE:** You cannot run both services simultaneously (Conflicts directive).

---

## Monitoring

### View Logs

```bash
# Guardian logs (includes worker output)
sudo journalctl -u sophia-guardian.service -f

# Worker logs (if using sophia-ami.service)
sudo journalctl -u sophia-ami.service -f

# Crash logs (Guardian only)
tail -f logs/guardian.log
tail -f logs/last_crash.log
ls -lth logs/crash_*.log | head -10
```

### Dashboard (Optional)

Start the monitoring dashboard:

```bash
# In separate terminal or screen/tmux session
cd /home/sophia/sophia
source .venv/bin/activate
python scripts/dashboard_server.py

# Access dashboard
# Open browser: http://localhost:8000/dashboard
```

Dashboard features:
- Real-time task queue status
- Task submission form
- Statistics (pending/done/failed)
- Auto-refresh every 5 seconds

---

## Task Submission

### Via Dashboard
1. Open `http://localhost:8000/dashboard`
2. Fill in "Instruction" field
3. Set priority (1-100, default 50)
4. Click "Submit Task"

### Via API

```bash
curl -X POST http://localhost:8000/api/enqueue \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Your task here", "priority": 50}'
```

### Via Python

```python
from core.simple_persistent_queue import SimplePersistentQueue

queue = SimplePersistentQueue('.data/tasks.sqlite')
task_id = queue.enqueue({
    'instruction': 'Your task description here'
}, priority=50)
print(f"Task enqueued: ID {task_id}")
```

---

## Service Management

### Start/Stop/Restart

```bash
# Start
sudo systemctl start sophia-guardian.service

# Stop
sudo systemctl stop sophia-guardian.service

# Restart
sudo systemctl restart sophia-guardian.service

# Status
sudo systemctl status sophia-guardian.service
```

### Auto-Start on Boot

```bash
# Enable
sudo systemctl enable sophia-guardian.service

# Disable
sudo systemctl disable sophia-guardian.service

# Check if enabled
systemctl is-enabled sophia-guardian.service
```

### Resource Limits

Configured in systemd unit file:
- **Memory:** 3GB max (Guardian + Worker combined)
- **CPU:** 90% quota
- **Restart:** Max 3 restarts in 10 minutes

Edit `/etc/systemd/system/sophia-guardian.service` to adjust limits.

---

## Crash Recovery

### Guardian Behavior

1. **Normal Crash (exit code ≠ 0):**
   - Save crash log to `logs/crash_YYYYMMDD_HHMMSS_exitN.log`
   - Update `logs/last_crash.log` symlink
   - Wait 5 seconds
   - Restart worker with `--recovery-from-crash` flag

2. **Crash Loop (5 crashes in 300s):**
   - Execute `git reset --hard HEAD~1` (rollback last commit)
   - Save rollback log
   - Restart worker from previous commit

3. **Guardian Crash:**
   - Systemd restarts Guardian itself (max 3 times in 10 min)

### Manual Recovery

If both services fail:

```bash
# Check logs
sudo journalctl -u sophia-guardian.service --since "1 hour ago"
cat logs/last_crash.log

# Reset to known good state
git log --oneline -10  # Find good commit
git reset --hard <commit-hash>

# Restart service
sudo systemctl restart sophia-guardian.service
```

---

## Validation Tests

### 1. Service Health Check

```bash
# Check if running
systemctl is-active sophia-guardian.service

# Check process tree
ps aux | grep -E "(guardian|autonomous_main)"

# Check resource usage
systemctl status sophia-guardian.service | grep -E "(Memory|CPU)"
```

### 2. Task Processing Test

```bash
# Enqueue test task
curl -X POST http://localhost:8000/api/enqueue \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Create file sandbox/test_production.txt with content: Production test successful", "priority": 50}'

# Wait 30 seconds, then check result
cat sandbox/test_production.txt
```

### 3. Crash Recovery Test

```bash
# Find worker PID
ps aux | grep autonomous_main.py | grep -v grep

# Kill worker (simulate crash)
kill -9 <PID>

# Watch logs - should see restart within 5 seconds
sudo journalctl -u sophia-guardian.service -f

# Check crash log created
ls -lth logs/crash_*.log | head -1
cat logs/last_crash.log
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check syntax
sudo systemd-analyze verify sophia-guardian.service

# Check permissions
ls -la /home/sophia/sophia/guardian.py
ls -la /home/sophia/sophia/scripts/autonomous_main.py

# Check Python path
/home/sophia/sophia/.venv/bin/python --version
```

### Worker Crashes Immediately

```bash
# Check environment variables
sudo journalctl -u sophia-guardian.service -n 100 | grep -i error

# Test worker manually
cd /home/sophia/sophia
source .venv/bin/activate
python scripts/autonomous_main.py
```

### Ollama Connection Issues

```bash
# Check Ollama status
systemctl status ollama

# Test Ollama API
curl http://localhost:11434/api/generate -d '{"model":"llama3.1:8b","prompt":"test"}'

# Check config/local_llm.yaml
cat config/local_llm.yaml
```

### High Memory/CPU Usage

```bash
# Check current usage
systemctl status sophia-guardian.service

# Adjust limits in service file
sudo nano /etc/systemd/system/sophia-guardian.service
# Modify MemoryMax= and CPUQuota=

sudo systemctl daemon-reload
sudo systemctl restart sophia-guardian.service
```

---

## Security Considerations

1. **User Isolation:** Service runs as `sophia` user (not root)
2. **Filesystem Access:** Limited to `/home/sophia/sophia/`
3. **Network:** Localhost only (Ollama on 127.0.0.1:11434)
4. **Privileges:** `NoNewPrivileges=true` prevents escalation
5. **Temp Files:** Isolated with `PrivateTmp=true`

**Production Hardening (Optional):**
- Enable firewall (ufw/iptables)
- Use AppArmor/SELinux profile
- Set up log rotation for `logs/` directory
- Enable disk quota for `sophia` user

---

## Maintenance

### Log Rotation

Create `/etc/logrotate.d/sophia`:

```
/home/sophia/sophia/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 sophia sophia
}
```

### Backup

Critical directories to backup:
- `.data/tasks.sqlite` (task queue)
- `sandbox/sophia_reflection_journal.md` (learning history)
- `config/` (configuration)
- `logs/` (optional, for forensics)

### Updates

```bash
# Stop service
sudo systemctl stop sophia-guardian.service

# Update code
cd /home/sophia/sophia
git pull

# Update dependencies
source .venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl start sophia-guardian.service

# Verify
sudo systemctl status sophia-guardian.service
```

---

## Performance Tuning

### Queue Processing Speed

Adjust worker poll interval in `scripts/autonomous_main.py`:

```python
worker = KernelWorker(kernel, queue, poll_interval=1.0)  # Default: 1s
```

### Crash Detection Sensitivity

Adjust Guardian parameters in service file:

```ini
ExecStart=... --max-crashes 5 --crash-window 300
# max-crashes: Number of crashes before rollback
# crash-window: Time window in seconds
```

### Resource Allocation

Based on typical workload:
- **Light (1-10 tasks/hour):** 1GB RAM, 50% CPU
- **Medium (10-50 tasks/hour):** 2GB RAM, 75% CPU
- **Heavy (50+ tasks/hour):** 3GB RAM, 90% CPU

---

## Production Checklist

- [ ] Ollama installed and running
- [ ] `llama3.1:8b` model pulled
- [ ] Repository cloned to `/home/sophia/sophia`
- [ ] Virtualenv created and dependencies installed
- [ ] Config files edited (local_llm.yaml)
- [ ] Directories created (logs/, sandbox/, .data/)
- [ ] Guardian service installed and enabled
- [ ] Service started successfully
- [ ] Test task processed successfully
- [ ] Crash recovery tested
- [ ] Log rotation configured
- [ ] Backup strategy in place
- [ ] Monitoring/alerting configured (optional)

---

## Support

- **Logs:** Check `logs/guardian.log` and `journalctl`
- **Documentation:** See `docs/` directory
- **Reflection Journal:** `sandbox/sophia_reflection_journal.md`
- **Issue Tracker:** GitHub repository

---

**Status:** Production deployment guide complete. System ready for 24/7 autonomous operation.

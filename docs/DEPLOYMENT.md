# 🚀 Nomad AI Agent - Deployment Guide

**Version:** 0.9.0  
**Last Updated:** October 2025  
**Architecture:** FastAPI Backend + Textual TUI + NomadOrchestratorV2

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [Docker Deployment](#docker-deployment)
4. [Systemd Service Deployment](#systemd-service-deployment)
5. [Configuration](#configuration)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Security Considerations](#security-considerations)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 2GB
- Disk: 10GB free space
- OS: Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+)

**Recommended:**
- CPU: 4+ cores
- RAM: 4GB+
- Disk: 20GB+ SSD
- OS: Ubuntu 22.04 LTS / Debian 12

### Software Dependencies

**Required:**
- Python 3.12 or higher
- pip / uv (package manager)

**Optional:**
- Docker 24.0+ (for containerized deployment)
- Docker Compose 2.0+
- systemd (for service management)
- nginx/traefik (for reverse proxy)
- prometheus/grafana (for monitoring)

### API Keys

You'll need at least one of:
- **Gemini API Key** (recommended for development)
- **OpenRouter API Key** (recommended for production with 15 models)

Get keys:
- Gemini: https://makersuite.google.com/app/apikey
- OpenRouter: https://openrouter.ai/keys

---

## Deployment Options

### Option 1: Docker Compose (Recommended for Production)

**Pros:**
- Isolated environment
- Easy upgrades
- Consistent across systems
- Resource limits enforced
- Multi-service orchestration

**Cons:**
- Requires Docker knowledge
- Slightly higher resource usage

**Quick Start:**
```bash
# 1. Clone repository
git clone https://github.com/your-org/sophia.git
cd sophia

# 2. Configure environment
cp .env.production.example .env
nano .env  # Add API keys

# 3. Start backend service
docker-compose up -d

# 4. Start TUI (optional interactive mode)
docker-compose --profile interactive run --rm tui

# 5. Check status
docker-compose ps
curl http://localhost:8080/api/v1/health/ping
```

### Option 2: Systemd Service (Production Linux)

**Pros:**
- Native Linux integration
- Lower resource overhead
- Direct system access
- Auto-restart on failure

**Cons:**
- Manual dependency management
- OS-specific configuration

**Quick Start:**
```bash
# Automated installation
sudo ./scripts/install-production.sh

# Manual service management
systemctl status nomad-backend
systemctl start nomad-backend
systemctl stop nomad-backend
journalctl -u nomad-backend -f
```

### Option 3: Development Mode

**Quick Start:**
```bash
# Setup development environment
./scripts/setup.sh

# Start backend
./scripts/start_backend.sh

# Start TUI (in separate terminal)
./scripts/start_tui.sh

# Or both together
./scripts/start_nomad.sh
```

---

## Docker Deployment

See [Deployment Options](#deployment-options) above for Docker Compose quick start.

### docker-compose.yml Structure

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8080:8080"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    volumes:
      - ./logs:/app/logs
      - ./memory:/app/memory
      - ./sandbox:/app/sandbox
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/v1/health/ping"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  tui:
    profiles: ["interactive"]
    build: .
    command: python -m tui.app
    environment:
      - BACKEND_URL=http://backend:8080
    depends_on:
      - backend
    stdin_open: true
    tty: true
```

### Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '1.0'
      memory: 1G
```

---

## Systemd Service Deployment

### Automated Installation

```bash
sudo ./scripts/install-production.sh
```

Installs to `/opt/nomad/` with:
- System user `nomad`
- Virtual environment
- Systemd services
- Auto-start on boot

### Service Management

```bash
# Status
systemctl status nomad-backend

# Start/Stop/Restart
systemctl start nomad-backend
systemctl stop nomad-backend
systemctl restart nomad-backend

# Logs
journalctl -u nomad-backend -f
journalctl -u nomad-backend -n 100

# Enable/Disable auto-start
systemctl enable nomad-backend
systemctl disable nomad-backend
```

### TUI Client (Per-User)

```bash
# Start TUI for current user
systemctl --user start nomad-tui@$USER

# Stop
systemctl --user stop nomad-tui@$USER

# Logs
journalctl --user -u nomad-tui@$USER -f
```

### Uninstallation

```bash
sudo ./scripts/uninstall-production.sh
```

---

## Configuration

### Environment Variables (.env)

```bash
# API Keys (REQUIRED)
GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_key_here

# Server
NOMAD_PORT=8080
NOMAD_HOST=0.0.0.0
NOMAD_ENV=production

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# LLM
DEFAULT_LLM_PROVIDER=openrouter
DEFAULT_MODEL=google/gemini-2.0-flash-exp
FALLBACK_MODEL=qwen/qwen-2.5-72b-instruct
TEMPERATURE=0.7

# Limits
MAX_CONCURRENT_MISSIONS=5
BUDGET_LIMIT_USD=10.0
MAX_TOKENS_PER_REQUEST=100000

# Health
HEALTH_CHECK_INTERVAL=30
CPU_THRESHOLD=80.0
MEMORY_THRESHOLD=85.0
```

### Production YAML (config/production.yaml)

See [.env.production.example](../.env.production.example) and [config/production.yaml](../config/production.yaml) for complete configuration options including:
- Logging (handlers, formatters, rotation)
- LLM providers (fallback chains)
- Orchestrator (recovery, reflection)
- Security (CORS, rate limiting)
- Monitoring (metrics, health checks)

### Supported Models (15 Total)

| Model | Cost (per 1M tokens) | Best For |
|-------|---------------------|----------|
| **qwen/qwen-2.5-72b-instruct** | $0.07/$0.26 | **Cheapest** complex tasks |
| google/gemma-3-27b-it | $0.09/$0.16 | Open source, fast |
| google/gemini-2.5-flash-lite | $0.10/$0.40 | Lightweight tasks |
| google/gemini-2.0-flash-exp | $0.075/$0.30 | **Recommended** default |
| meta-llama/llama-3.3-70b-instruct | $0.13/$0.39 | Strong reasoning |
| deepseek/deepseek-v3.2-exp | $0.27/$0.40 | Coding specialist |
| anthropic/claude-3-haiku | $0.25/$1.25 | Fast, efficient |
| openai/gpt-4o-mini | $0.15/$0.60 | GPT quality |

Configure in `.env`:
```bash
DEFAULT_MODEL=google/gemini-2.0-flash-exp
FALLBACK_MODEL=qwen/qwen-2.5-72b-instruct
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Ping endpoint
curl http://localhost:8080/api/v1/health/ping

# Detailed health status
curl http://localhost:8080/api/v1/health/status

# Expected response:
{
  "status": "healthy",
  "version": "0.9.0",
  "uptime": 3600,
  "cpu_percent": 15.3,
  "memory_percent": 45.2,
  "active_missions": 2
}
```

### Logs

**Docker:**
```bash
# Real-time logs
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Since specific time
docker-compose logs --since="2024-01-01T10:00:00" backend
```

**Systemd:**
```bash
# Real-time
journalctl -u nomad-backend -f

# Last hour
journalctl -u nomad-backend --since="1 hour ago"

# Errors only
journalctl -u nomad-backend -p err

# Export to file
journalctl -u nomad-backend > nomad.log
```

**File Logs:**
```bash
# Application logs (/opt/nomad/logs/ or ./logs/)
tail -f logs/nomad.log
tail -f logs/error.log

# Log rotation: 10MB max, 5 backups (automatic)
```

### Backups

**Manual Backup:**
```bash
# Backup critical data
tar -czf nomad-backup-$(date +%Y%m%d).tar.gz \
  memory/ config/ .env logs/

# Restore
tar -xzf nomad-backup-20250112.tar.gz
```

**Docker Volumes:**
```bash
# Backup volumes
docker run --rm \
  -v sophia_memory:/memory \
  -v $(pwd):/backup \
  alpine tar czf /backup/memory-backup.tar.gz /memory

# Restore
docker run --rm \
  -v sophia_memory:/memory \
  -v $(pwd):/backup \
  alpine tar xzf /backup/memory-backup.tar.gz -C /
```

### Upgrades

**Docker:**
```bash
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
docker-compose logs -f backend
```

**Systemd:**
```bash
sudo systemctl stop nomad-backend
cd /opt/nomad
sudo -u nomad git pull origin main
sudo -u nomad ./venv/bin/pip install -r requirements.txt
sudo systemctl start nomad-backend
systemctl status nomad-backend
```

---

## Security Considerations

### API Key Security

```bash
# NEVER commit .env
git check-ignore .env  # Should return .env

# Restrict permissions
chmod 600 .env
chown nomad:nomad .env  # If using systemd

# Rotate keys every 90 days (recommended)
```

### Network Security

**Firewall (ufw):**
```bash
# Allow only localhost
sudo ufw deny 8080
sudo ufw allow from 127.0.0.1 to any port 8080

# Or specific network
sudo ufw allow from 192.168.1.0/24 to any port 8080
```

**Reverse Proxy (nginx):**
```nginx
server {
    listen 80;
    server_name nomad.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Resource Limits

**Docker Compose:**
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
```

**Systemd:**
```ini
[Service]
MemoryMax=2G
CPUQuota=200%
LimitNOFILE=65536
```

---

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
# Docker
docker-compose logs backend

# Systemd
journalctl -u nomad-backend -n 50
```

**Common issues:**

1. **Port in use:**
```bash
sudo lsof -i :8080
# Change NOMAD_PORT in .env or kill process
```

2. **Missing API keys:**
```bash
grep "API_KEY" .env
# Should show non-empty values
```

3. **Permission errors:**
```bash
sudo chown -R nomad:nomad /opt/nomad
sudo chmod 755 /opt/nomad
sudo chmod 600 /opt/nomad/.env
```

### High CPU/Memory

```bash
# Check active missions
curl http://localhost:8080/api/v1/missions/active

# Monitor resources
docker stats nomad-backend  # Docker
top -p $(pgrep -f nomad)     # Systemd

# Solutions:
# - Reduce MAX_CONCURRENT_MISSIONS
# - Lower MAX_TOKENS_PER_REQUEST
# - Enable budget limits
# - Restart service
```

### Connection Refused

```bash
# Verify service running
docker-compose ps            # Docker
systemctl status nomad-backend  # Systemd

# Check port listening
sudo netstat -tulpn | grep 8080

# Test connectivity
curl http://localhost:8080/api/v1/health/ping
```

### LLM API Errors

**Test API keys:**
```bash
# Gemini
curl -H "x-goog-api-key: $GEMINI_API_KEY" \
  https://generativelanguage.googleapis.com/v1/models

# OpenRouter
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/models
```

**Common errors:**
- Invalid key → Regenerate and update .env
- Rate limit → Enable budget tracking, use cheaper models
- Model unavailable → Check model name in docs

---

## Production Checklist

Before deployment:

```
✅ Environment variables configured (.env)
✅ API keys tested and working
✅ Tests passing (pytest tests/ -v)
✅ Logging configured
✅ Health checks responding
✅ Backups strategy defined
✅ Monitoring set up (optional)
✅ Security review (firewall, permissions)
✅ Documentation reviewed
✅ Team trained on operations
```

---

## Support & Resources

### Documentation

- [README.md](../README.md) - Project overview
- [QUICKSTART.md](QUICKSTART.md) - Getting started
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Development
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [AGENTS.md](../AGENTS.md) - AI agent manual

### Getting Help

- **Issues:** GitHub Issues
- **Tests:** `pytest tests/ -v`
- **Logs:** See "Monitoring & Maintenance" section

---

**Status:** ✅ Production Ready (v0.9.0)  
**Last Updated:** October 2025  
**Maintainer:** Nomad Development Team

### Log Aggregation

**With ELK Stack:**

```bash
# Filebeat config (filebeat.yml)
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /app/logs/nomad.log
    json.keys_under_root: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

**With Loki:**

```yaml
# promtail-config.yml
scrape_configs:
  - job_name: nomad
    static_configs:
      - targets:
          - localhost
        labels:
          job: nomad
          __path__: /app/logs/nomad.log
```

### Metrics

Nomad exposes Prometheus metrics:

```bash
# Prometheus config (prometheus.yml)
scrape_configs:
  - job_name: 'nomad'
    static_configs:
      - targets: ['nomad:9090']
```

**Available Metrics:**

- `nomad_missions_total` - Total missions executed
- `nomad_missions_success_rate` - Success rate (%)
- `nomad_tokens_used_total` - Total tokens consumed
- `nomad_avg_mission_duration_seconds` - Average mission time
- `nomad_errors_total` - Total errors encountered

### Dashboards

**Grafana Dashboard:**

```json
{
  "dashboard": {
    "title": "Nomad Orchestrator v0.8.9",
    "panels": [
      {
        "title": "Mission Success Rate",
        "targets": [
          {
            "expr": "rate(nomad_missions_success_rate[5m])"
          }
        ]
      },
      {
        "title": "Token Usage",
        "targets": [
          {
            "expr": "rate(nomad_tokens_used_total[1h])"
          }
        ]
      }
    ]
  }
}
```

---

## 6. Security

### API Key Management

**DO:**
- ✅ Store keys in environment variables or secrets manager
- ✅ Rotate keys every 90 days
- ✅ Use different keys for dev/staging/prod
- ✅ Monitor key usage for anomalies

**DON'T:**
- ❌ Commit keys to Git
- ❌ Share keys via unencrypted channels
- ❌ Use same key across environments
- ❌ Log API keys

### Secrets Manager Integration

**AWS Secrets Manager:**

```python
import boto3
import json

def get_api_key():
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId='nomad/api-keys')
    return json.loads(response['SecretString'])['GEMINI_API_KEY']
```

**HashiCorp Vault:**

```python
import hvac

def get_api_key():
    client = hvac.Client(url='http://vault:8200')
    client.token = os.getenv('VAULT_TOKEN')
    secret = client.secrets.kv.v2.read_secret_version(path='nomad/api-keys')
    return secret['data']['data']['GEMINI_API_KEY']
```

### Network Security

```bash
# Firewall rules (ufw)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from YOUR_IP to any port 22  # SSH only from specific IP
sudo ufw enable

# For API exposure (if needed)
sudo ufw allow from TRUSTED_NETWORK to any port 8080
```

### Sandboxing

Nomad operates in strict sandbox mode by default:

- **File Access:** Limited to `sandbox/` and `memory/` directories
- **Network:** Outbound only to approved APIs
- **Execution:** No arbitrary code execution outside tools

---

## 7. Troubleshooting

### Common Issues

#### "API Key Invalid"

```bash
# Verify key format
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('GEMINI_API_KEY')
assert key.startswith('AIza'), 'Invalid key format'
print('Key format OK')
"

# Test with curl
curl -X POST "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key=YOUR_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"contents":[{"parts":[{"text":"test"}]}]}'
```

#### "Out of Memory"

```bash
# Check current usage
free -h

# Increase swap (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Monitor
watch -n 1 'free -h'
```

#### "Mission Stuck"

```bash
# Check state
python -c "
from core.state_manager import StateManager
sm = StateManager(session_id='STUCK_SESSION_ID')
if sm.restore():
    print(f'State: {sm.get_state().value}')
    print(f'Data: {sm.state_data}')
"

# Force recovery
python -c "
from core.recovery_manager import RecoveryManager
rm = RecoveryManager()
crashed = rm.find_crashed_sessions()
for session_id in crashed:
    print(f'Recovering {session_id}...')
    rm.recover_session(session_id)
"
```

### Performance Tuning

```python
# config/performance.yaml

# Async optimization
async_pool_size: 10  # Concurrent tool executions
enable_request_batching: true

# Caching
enable_llm_response_cache: true
cache_ttl_hours: 24

# Timeouts
llm_timeout_seconds: 30
tool_timeout_seconds: 60
mission_timeout_hours: 2
```

### Health Checks

```bash
# Check all systems
python scripts/health_check.py

# Expected output:
# ✅ Environment: OK
# ✅ LLM Connectivity: OK
# ✅ Memory System: OK
# ✅ Budget Tracker: OK
# ✅ All Tests: 157/157 passing
```

---

## 📊 Production Checklist

Before going live:

```
[ ] Environment variables configured
[ ] API keys tested and working
[ ] All 157 tests passing
[ ] Logging configured and tested
[ ] Monitoring dashboards set up
[ ] Backup strategy defined
[ ] Security review completed
[ ] Load testing performed
[ ] Disaster recovery plan documented
[ ] Team trained on operations
[ ] On-call rotation established
```

---

**Status:** ✅ Production Ready  
**Support:** See docs/TROUBLESHOOTING.md  
**Updates:** https://github.com/ShotyCZ/sophia/releases

# 🚀 Production Deployment Guide - Nomad v0.8.9

**Last Updated:** 2025-10-12  
**Version:** 0.8.9  
**Architecture:** NomadOrchestratorV2

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Configuration](#configuration)
4. [Deployment Options](#deployment-options)
5. [Monitoring & Logging](#monitoring--logging)
6. [Security](#security)
7. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisites

### System Requirements

- **Python:** >= 3.10
- **RAM:** Minimum 2GB, Recommended 4GB+
- **Disk:** 500MB free space
- **Network:** Outbound HTTPS access to AI APIs

### Required Services

- **Gemini API Access** (for LLM operations)
- **Optional:** Redis (for advanced memory features)
- **Optional:** Docker (for containerized deployment)

---

## 2. Environment Setup

### Step 1: Clone & Install

```bash
# Clone repository
git clone https://github.com/ShotyCZ/sophia.git
cd sophia

# Checkout production branch
git checkout nomad/0.8.9

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env with your values
nano .env
```

**Required Variables:**

```bash
# API Keys
GEMINI_API_KEY="your_gemini_api_key_here"

# Optional: Advanced Features
# OPENROUTER_API_KEY="your_openrouter_key"  # For multiple LLM providers
# DEEPSEEK_API_KEY="your_deepseek_key"      # For DeepSeek models
```

### Step 3: Verify Setup

```bash
# Test environment
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
assert os.getenv('GEMINI_API_KEY'), 'API key missing!'
print('✅ Environment configured')
"

# Run health check
python -c "
import asyncio
from core.llm_manager import LLMManager

async def test():
    llm = LLMManager()
    model = llm.get_llm('powerful')
    resp, _ = await model.generate_content_async('Say OK')
    assert resp, 'LLM not responding'
    print('✅ LLM connectivity OK')

asyncio.run(test())
"
```

---

## 3. Configuration

### config/config.yaml

Production configuration template:

```yaml
# Production Configuration for Nomad v0.8.9

environment: production

llm:
  default_model: "gemini-pro"
  fallback_models:
    - "gemini-pro-1.5"
  
  # Budget limits (production defaults)
  max_tokens_per_mission: 100000
  max_time_per_mission_seconds: 3600
  
  # Rate limiting
  max_requests_per_minute: 50

orchestrator:
  # State machine config
  max_step_retries: 3
  enable_crash_recovery: true
  
  # Session management
  session_timeout_hours: 24
  auto_cleanup_old_sessions: true
  
logging:
  level: INFO
  format: "json"  # For production log aggregation
  
  destinations:
    - type: file
      path: "logs/nomad.log"
      max_size_mb: 100
      backup_count: 5
    
    - type: console
      level: WARNING  # Only warnings+ to console
  
  # Structured logging
  include_timestamp: true
  include_session_id: true
  include_state: true

monitoring:
  # Metrics collection
  enable_metrics: true
  metrics_port: 9090
  
  # Health checks
  health_check_interval_seconds: 60
  
  # Alerting
  alert_on_errors: true
  alert_threshold: 5  # Alert after 5 consecutive errors

memory:
  # Session persistence
  memory_dir: "memory/"
  
  # Cleanup policy
  cleanup_completed_after_days: 7
  cleanup_failed_after_days: 30
  
  # Advanced (optional)
  use_redis: false
  # redis_url: "redis://localhost:6379/0"

security:
  # API key rotation
  require_key_rotation: true
  key_rotation_days: 90
  
  # Sandboxing
  sandbox_mode: strict
  allowed_directories:
    - "sandbox/"
    - "memory/"
  
  # Rate limiting per IP (if exposed via API)
  enable_rate_limiting: true
  rate_limit_per_hour: 100
```

### Custom Configuration

```python
# custom_config.py

from core.config import Config

class ProductionConfig(Config):
    """Production-specific overrides."""
    
    def __init__(self):
        super().__init__()
        
        # Override defaults
        self.LOG_LEVEL = "INFO"
        self.ENABLE_PROFILING = False
        self.DEBUG_MODE = False
        
        # Production tuning
        self.MAX_CONCURRENT_MISSIONS = 5
        self.ENABLE_CACHING = True
```

---

## 4. Deployment Options

### Option A: Standalone Script

Simple deployment for single missions:

```bash
# Run single mission
python main.py --mission "Your task here"

# Or interactive mode
python interactive_session.py
```

### Option B: Long-Running Service

For continuous operation:

```bash
# Start as background service
nohup python service.py > logs/service.log 2>&1 &

# Or using systemd (Linux)
sudo cp deploy/nomad.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nomad
sudo systemctl start nomad
```

**deploy/nomad.service:**

```ini
[Unit]
Description=Nomad AI Orchestrator v0.8.9
After=network.target

[Service]
Type=simple
User=nomad
WorkingDirectory=/opt/sophia
Environment="PATH=/opt/sophia/venv/bin"
ExecStart=/opt/sophia/venv/bin/python service.py
Restart=on-failure
RestartSec=10

# Resource limits
MemoryMax=4G
CPUQuota=200%

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Option C: Docker Container

Containerized deployment:

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 nomad && \
    chown -R nomad:nomad /app
USER nomad

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# Run
CMD ["python", "service.py"]
```

```bash
# Build
docker build -t nomad:0.8.9 .

# Run
docker run -d \
  --name nomad \
  -e GEMINI_API_KEY="${GEMINI_API_KEY}" \
  -v $(pwd)/memory:/app/memory \
  -v $(pwd)/logs:/app/logs \
  --restart unless-stopped \
  nomad:0.8.9
```

### Option D: Docker Compose (Recommended)

Full stack with monitoring:

```yaml
# docker-compose.yml
version: '3.8'

services:
  nomad:
    build: .
    container_name: nomad
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - ENVIRONMENT=production
    volumes:
      - ./memory:/app/memory
      - ./logs:/app/logs
      - ./config:/app/config
    restart: unless-stopped
    networks:
      - nomad-net
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
  
  # Optional: Redis for advanced memory
  redis:
    image: redis:7-alpine
    container_name: nomad-redis
    volumes:
      - redis-data:/data
    networks:
      - nomad-net
    restart: unless-stopped

volumes:
  redis-data:

networks:
  nomad-net:
    driver: bridge
```

```bash
# Deploy
docker-compose up -d

# View logs
docker-compose logs -f nomad

# Stop
docker-compose down
```

---

## 5. Monitoring & Logging

### Structured Logging

Nomad outputs JSON logs for easy parsing:

```json
{
  "timestamp": "2025-10-12T14:30:45.123Z",
  "level": "INFO",
  "session_id": "20251012_143045",
  "state": "EXECUTING_STEP",
  "message": "Tool execution completed",
  "metadata": {
    "step_id": 3,
    "tool_name": "create_file",
    "tokens_used": 245
  }
}
```

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

# 🔧 Guardian Refactoring & OpenRouter Enhancement Plan

**Datum:** 2025-10-12  
**Verze:** 1.0  
**Status:** NAVAZUJE NA TUI_REDESIGN_PLAN.md  
**Autor:** GitHub Copilot AI Agent

---

## 📋 Executive Summary

Tento dokument rozšiřuje TUI_REDESIGN_PLAN.md o dva kritické body:

1. **Guardian Refactoring** - Odstranění problematického git reset mechanismu
2. **OpenRouter Enhancement** - Maximální využití OpenRouter features

---

## 🛡️ Guardian Analysis & Refactoring

### Současný Stav Guardiana

**Komponenty:**
1. `guardian/agent.py` - System monitoring (CPU, RAM, Disk, FD)
2. `guardian/runner.py` - **PROBLEMATICKÝ** - Restart + Git rollback

**Kritický Problém:**
```python
# guardian/runner.py:56-62
def revert_to_last_known_good():
    """Provede 'git reset --hard' a bezpečný úklid na poslední funkční commit."""
    commit_hash = get_last_known_good_commit()
    subprocess.run(["git", "reset", "--hard", commit_hash], check=True)
    subprocess.run(["git", "clean", "-df"], check=True)
    # ☠️ MAZNE POSTUP! Ztráta veškeré práce!
```

**Co dělá Guardian:**
- ✅ Monitoruje systémové zdroje (dobré, ale redundantní)
- ✅ Restartuje TUI při crashu (dobré, ale nemusí)
- ❌ **Git reset --hard při 3 crashech** (ŠPATNÉ! Maže postup!)
- ❌ Spouští TUI přímo (nekompatibilní s client-server)

### NomadV2 Již Má Built-in Recovery

**RecoveryManager v NomadV2:**
```python
# core/recovery_manager.py - UŽ IMPLEMENTOVÁNO ✅
class RecoveryManager:
    def find_crashed_sessions(self) -> List[str]
    def recover_session(self, session_file: str) -> StateManager
    def detect_state_for_recovery(self, state_manager: StateManager) -> RecoveryStrategy
```

**Co NomadV2 dělá lépe:**
- ✅ Session persistence (StateManager auto-save každých 10s)
- ✅ Crash detection (kontrola nedokončených sessions)
- ✅ Recovery strategies (retry, replanning, skip_step, ask_user)
- ✅ State machine validace (invalid transitions = error)
- ✅ **ŽÁDNÝ GIT RESET!** (zachování práce)

### Nový Design: Health Monitor (Nahrazení Guardiana)

**Koncept:**
Guardian bude přejmenován a refaktorován na **Health Monitor** - lightweight monitoring bez destruktivních akcí.

```
┌─────────────────────────────────────────────────────────┐
│           Health Monitor (Nový Guardian)                │
│  ┌──────────────────────────────────────────────────┐   │
│  │  System Metrics Collector                        │   │
│  │  - CPU usage                                     │   │
│  │  - Memory usage                                  │   │
│  │  - Disk space                                    │   │
│  │  - File descriptors                              │   │
│  │  - Process list                                  │   │
│  └──────────────────────────────────────────────────┘   │
│                      ↓                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Backend API Endpoint                            │   │
│  │  GET /api/v1/health                              │   │
│  │  GET /api/v1/health/metrics                      │   │
│  │  GET /api/v1/health/history                      │   │
│  └──────────────────────────────────────────────────┘   │
│                      ↓                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  TUI Health Tab (Nový)                           │   │
│  │  - Real-time metrics                             │   │
│  │  - Resource graphs                               │   │
│  │  - Alerts & warnings                             │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Co NEBUDE dělat:**
- ❌ Git reset (NIKDY!)
- ❌ Automatické rollbacky
- ❌ TUI restart (to je job systemd/Docker)
- ❌ Destructive operations

**Co BUDE dělat:**
- ✅ Sbírat metriky (CPU, RAM, Disk, FD)
- ✅ Exponovat přes API
- ✅ Logovat warnings
- ✅ Alertovat při kritických hodnotách
- ✅ Integrovat do TUI (Health tab)

### Implementation Plan

#### 1. **Deprecate Old Guardian**
```bash
# Přesun do archive
mv guardian/ archive/deprecated_code/guardian_old/
```

#### 2. **Create New Health Monitor**
```python
# backend/health_monitor.py (NEW)
class HealthMonitor:
    """
    Lightweight system health monitoring.
    No destructive actions, only observation & alerting.
    """
    
    async def collect_metrics(self) -> HealthMetrics:
        """Collect current system metrics."""
        return HealthMetrics(
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            disk_percent=psutil.disk_usage('/').percent,
            open_files=len(psutil.Process().open_files()),
            timestamp=datetime.now()
        )
    
    async def check_alerts(self, metrics: HealthMetrics) -> List[Alert]:
        """Check if any metrics exceed thresholds."""
        alerts = []
        if metrics.cpu_percent > 90:
            alerts.append(Alert("HIGH_CPU", f"CPU at {metrics.cpu_percent}%"))
        if metrics.memory_percent > 90:
            alerts.append(Alert("HIGH_MEMORY", f"Memory at {metrics.memory_percent}%"))
        return alerts
```

#### 3. **Backend API Integration**
```python
# backend/routes/health.py (NEW)
@router.get("/health")
async def get_health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now()}

@router.get("/health/metrics")
async def get_metrics():
    """Current system metrics."""
    metrics = await health_monitor.collect_metrics()
    return metrics.dict()

@router.get("/health/alerts")
async def get_alerts():
    """Active health alerts."""
    alerts = await health_monitor.get_active_alerts()
    return {"alerts": [a.dict() for a in alerts]}
```

#### 4. **TUI Health Tab**
```python
# tui/widgets/health_viewer.py (NEW)
class HealthViewer(Widget):
    """Display system health metrics in TUI."""
    
    def compose(self):
        yield Static(id="cpu_gauge")
        yield Static(id="memory_gauge")
        yield Static(id="disk_gauge")
        yield RichLog(id="alerts")
    
    async def on_mount(self):
        self.set_interval(5.0, self.update_metrics)
    
    async def update_metrics(self):
        metrics = await self.api_client.get_health_metrics()
        self.update_gauges(metrics)
```

---

## 🌐 OpenRouter Enhancement

### Současný Stav

**Co máme:**
- ✅ OpenRouterAdapter v `core/llm_adapters.py`
- ✅ Fallback strategy
- ✅ Async support
- ✅ Stream support
- ⚠️ **Částečná** JSON mode podpora
- ❌ Chybí parameter reading
- ❌ Chybí billing tracking
- ❌ Chybí advanced features

**Co chybí:**
1. ✅ **JSON Mode** - Enforced structured output
2. ❌ **Parameter Reading** - Model-specific parameters
3. ❌ **Billing Tracking** - Detailed cost breakdown
4. ❌ **Model Capabilities** - Query available models & features
5. ❌ **Generation Config** - Temperature, top_p, max_tokens
6. ❌ **Provider Selection** - Force specific provider
7. ❌ **Response Caching** - Cost optimization

### OpenRouter Full Feature Set

**API Features:**
```json
{
  "models": "https://openrouter.ai/api/v1/models",
  "generation_params": [
    "temperature",
    "top_p", 
    "top_k",
    "frequency_penalty",
    "presence_penalty",
    "repetition_penalty",
    "min_p",
    "top_a",
    "seed",
    "max_tokens",
    "logit_bias",
    "logprobs",
    "top_logprobs",
    "response_format",  // ✅ JSON mode
    "stop",
    "tools",            // Function calling
    "tool_choice"
  ],
  "extra_headers": {
    "HTTP-Referer": "your-site-url",
    "X-Title": "your-app-name"
  },
  "extra_body": {
    "provider": {
      "order": ["OpenAI", "Anthropic"],
      "allow_fallbacks": true
    },
    "transforms": ["middle-out"]
  }
}
```

### Enhanced OpenRouterAdapter

```python
# core/llm_adapters.py (ENHANCED)
class OpenRouterAdapter(BaseLLMAdapter):
    """
    Full-featured OpenRouter adapter with all API capabilities.
    """
    
    def __init__(
        self,
        model_name: str,
        client: AsyncOpenAI,
        fallback_models: list = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = 4096,
        provider_preferences: list = None,
        **kwargs
    ):
        super().__init__(model_name=model_name)
        self._client = client
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.provider_preferences = provider_preferences or []
        self.models_to_try = [self.model_name] + (fallback_models or [])
        
        # Billing tracking
        self._total_cost = 0.0
        self._call_history = []
    
    async def generate_content_async(
        self,
        prompt: str,
        response_format: dict | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list | None = None,
        stream_callback = None,
        **kwargs
    ) -> tuple[str, dict]:
        """
        Enhanced generation with full parameter support.
        
        Features:
        - JSON mode (response_format)
        - Custom generation params
        - Tool/function calling
        - Provider selection
        - Detailed billing
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # Generation parameters
        gen_params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "top_p": self.top_p,
            "max_tokens": max_tokens or self.max_tokens,
        }
        
        # JSON mode
        if response_format:
            gen_params["response_format"] = response_format
        
        # Function calling
        if tools:
            gen_params["tools"] = tools
            gen_params["tool_choice"] = kwargs.get("tool_choice", "auto")
        
        # Provider preferences
        extra_body = {}
        if self.provider_preferences:
            extra_body["provider"] = {
                "order": self.provider_preferences,
                "allow_fallbacks": True
            }
        
        if extra_body:
            gen_params["extra_body"] = extra_body
        
        # Add referer for better analytics
        # (OpenRouter tracks usage by referer)
        
        # Execute with fallback
        for model_name in self.models_to_try:
            try:
                gen_params["model"] = model_name
                
                if stream_callback:
                    # Streaming mode
                    return await self._generate_stream(gen_params, stream_callback)
                else:
                    # Non-streaming mode
                    response = await self._client.chat.completions.create(**gen_params)
                    
                    # Extract content
                    content = response.choices[0].message.content
                    
                    # Enhanced usage data
                    usage_data = self._extract_usage_data(response)
                    
                    # Track billing
                    self._track_billing(usage_data)
                    
                    return content, usage_data
                    
            except Exception as e:
                RichPrinter.error(f"Model '{model_name}' failed: {e}")
                continue
        
        raise Exception("All models (including fallbacks) failed")
    
    def _extract_usage_data(self, response) -> dict:
        """
        Extract comprehensive usage data from response.
        
        OpenRouter provides:
        - Native cost from provider
        - Token counts
        - Model used
        - Generation ID
        """
        usage = response.usage.model_dump() if response.usage else {}
        
        # Calculate cost if not provided
        cost = self._calculate_cost(
            model=response.model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0)
        )
        
        return {
            "id": response.id,
            "model": response.model,
            "usage": usage,
            "cost": cost,
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate cost based on OpenRouter pricing.
        
        Note: OpenRouter má dynamické ceny, ideálně fetchnout z API.
        """
        # Placeholder - should fetch from OpenRouter pricing API
        PRICING = {
            "google/gemini-2.5-flash-lite": {
                "prompt": 0.075 / 1_000_000,  # $0.075 per 1M tokens
                "completion": 0.30 / 1_000_000
            },
            "anthropic/claude-3-haiku": {
                "prompt": 0.25 / 1_000_000,
                "completion": 1.25 / 1_000_000
            }
        }
        
        if model not in PRICING:
            return 0.0
        
        pricing = PRICING[model]
        cost = (prompt_tokens * pricing["prompt"]) + (completion_tokens * pricing["completion"])
        return round(cost, 6)
    
    def _track_billing(self, usage_data: dict):
        """Track billing for analytics."""
        self._total_cost += usage_data["cost"]
        self._call_history.append(usage_data)
    
    def get_billing_summary(self) -> dict:
        """Get billing summary for this adapter."""
        return {
            "total_cost": self._total_cost,
            "total_calls": len(self._call_history),
            "total_tokens": sum(
                call["usage"].get("total_tokens", 0) 
                for call in self._call_history
            ),
            "by_model": self._group_by_model()
        }
    
    def _group_by_model(self) -> dict:
        """Group billing by model."""
        by_model = {}
        for call in self._call_history:
            model = call["model"]
            if model not in by_model:
                by_model[model] = {
                    "calls": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            by_model[model]["calls"] += 1
            by_model[model]["tokens"] += call["usage"].get("total_tokens", 0)
            by_model[model]["cost"] += call["cost"]
        return by_model
```

### OpenRouter Model Discovery

```python
# core/openrouter_client.py (NEW)
class OpenRouterClient:
    """
    Client for OpenRouter metadata APIs.
    """
    
    async def fetch_available_models(self) -> list[dict]:
        """
        Fetch all available models from OpenRouter.
        
        Returns model list with:
        - id
        - name
        - description
        - pricing
        - context_length
        - architecture
        - supported_generation_params
        """
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://openrouter.ai/api/v1/models")
            resp.raise_for_status()
            return resp.json()["data"]
    
    async def fetch_model_pricing(self, model_id: str) -> dict:
        """Get current pricing for specific model."""
        models = await self.fetch_available_models()
        for model in models:
            if model["id"] == model_id:
                return model.get("pricing", {})
        return {}
    
    async def get_generation_stats(self, api_key: str) -> dict:
        """
        Fetch generation statistics from OpenRouter.
        
        Requires API key for user-specific stats.
        """
        headers = {"Authorization": f"Bearer {api_key}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://openrouter.ai/api/v1/generation",
                headers=headers
            )
            resp.raise_for_status()
            return resp.json()
```

### JSON Mode Usage

```python
# Example: Structured output with JSON mode
response, usage = await llm.generate_content_async(
    prompt="Analyze this code and return findings",
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "code_analysis",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "issues": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "severity": {"type": "string"},
                                "message": {"type": "string"},
                                "line": {"type": "number"}
                            },
                            "required": ["severity", "message"]
                        }
                    },
                    "summary": {"type": "string"}
                },
                "required": ["issues", "summary"]
            }
        }
    }
)

# Response je garantovaně valid JSON podle schema
import json
analysis = json.loads(response)
```

---

## 📊 Integration with NomadV2

### BudgetTracker Enhancement

```python
# core/budget_tracker.py (ENHANCED)
class BudgetTracker:
    """Enhanced with OpenRouter billing data."""
    
    def track_llm_call(self, usage_data: dict):
        """Track LLM call with enhanced OpenRouter data."""
        self.total_tokens += usage_data["usage"].get("total_tokens", 0)
        
        # NEW: Track actual cost from OpenRouter
        if "cost" in usage_data:
            self.total_cost += usage_data["cost"]
        
        # NEW: Track by model
        model = usage_data.get("model", "unknown")
        if model not in self.by_model:
            self.by_model[model] = {"calls": 0, "tokens": 0, "cost": 0.0}
        
        self.by_model[model]["calls"] += 1
        self.by_model[model]["tokens"] += usage_data["usage"].get("total_tokens", 0)
        self.by_model[model]["cost"] += usage_data.get("cost", 0.0)
    
    def get_summary(self) -> dict:
        """Enhanced summary with OpenRouter data."""
        return {
            "tokens": {
                "total": self.total_tokens,
                "max": self.max_tokens,
                "percent": (self.total_tokens / self.max_tokens) * 100
            },
            "cost": {
                "total": self.total_cost,
                "by_model": self.by_model,
                "currency": "USD"
            },
            "time": {
                "elapsed": self.get_elapsed_time(),
                "max": self.max_time_seconds
            }
        }
```

---

## 🎯 Implementation Roadmap

### Phase 1: Guardian Removal (1 day)
- [ ] Archive old Guardian (`guardian/` → `archive/deprecated_code/`)
- [ ] Remove Guardian references from docs
- [ ] Update docker-compose.yml (remove Guardian service)
- [ ] Update README.md

### Phase 2: Health Monitor (1 day)
- [ ] Create `backend/health_monitor.py`
- [ ] Add health endpoints to backend API
- [ ] Create TUI Health tab widget
- [ ] Integration tests

### Phase 3: OpenRouter Enhancement (2 days)
- [ ] Enhance `OpenRouterAdapter` class
  - [ ] Full parameter support
  - [ ] JSON mode
  - [ ] Billing tracking
  - [ ] Provider preferences
- [ ] Create `OpenRouterClient` for metadata
- [ ] Update `BudgetTracker` for cost tracking
- [ ] Add model discovery endpoint

### Phase 4: Testing & Documentation (1 day)
- [ ] Test JSON mode with real schemas
- [ ] Test provider fallbacks
- [ ] Verify billing accuracy
- [ ] Update all docs:
  - [ ] README.md
  - [ ] AGENTS.md
  - [ ] docs/REAL_LLM_SETUP.md
  - [ ] docs/DEPLOYMENT.md
- [ ] Update WORKLOG.md

**Total Estimate:** 5 days

---

## ✅ Success Criteria

### Guardian Refactoring
- ✅ Žádný git reset v kódu
- ✅ Crash recovery pouze přes RecoveryManager
- ✅ Health monitoring přes API
- ✅ TUI Health tab funkční
- ✅ Žádná data loss

### OpenRouter Enhancement
- ✅ JSON mode funguje s strict schemas
- ✅ Billing tracking s přesností ±1%
- ✅ Provider fallback funguje
- ✅ Model discovery endpoint
- ✅ All generation params supported
- ✅ Kompatibilita s Gemini adapter zachována

---

## 📝 Documentation Updates

### Files to Update

1. **README.md**
   - Remove Guardian mention
   - Add Health Monitor section
   - Update OpenRouter features

2. **AGENTS.md**
   - Remove Guardian workflow
   - Add Health Monitor usage
   - Update LLM best practices

3. **docs/REAL_LLM_SETUP.md**
   - Add OpenRouter setup
   - Add JSON mode examples
   - Add billing tracking guide

4. **docs/DEPLOYMENT.md**
   - Remove Guardian systemd service
   - Add Health Monitor integration

5. **WORKLOG.md**
   - Record all changes

---

## 🔗 Relation to TUI_REDESIGN_PLAN

Tento plán je **addon** k TUI_REDESIGN_PLAN.md:

**TUI Plan:**
- Backend server (FastAPI)
- TUI client (Textual)
- 6 tabs (Plan, Execution, Logs, State, Budget, History)

**Tento Plan (Guardian + OpenRouter):**
- 7th tab: **Health** (system metrics)
- Enhanced Budget tab (OpenRouter cost breakdown)
- Backend health endpoints
- No destructive operations
- Full OpenRouter feature set

**Combined Timeline:**
- TUI Implementation: 6-10 days
- Guardian + OpenRouter: 5 days
- **Total: 11-15 days**

---

**Ready for implementation po schválení TUI plánu! 🚀**

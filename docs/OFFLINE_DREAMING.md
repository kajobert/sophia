# Offline Dreaming & Self-Improvement Architecture

**Version:** 1.0.0  
**Status:** 🚧 DESIGN PHASE  
**Author:** Sophia AGI Team

---

## 🎯 Vision

Enable Sophia to:
1. **Operate fully offline** using local Llama 3.1 8B during "sleep" cycles
2. **Track model signatures** - record which LLM performed each operation
3. **Self-evaluate** - when online, assess quality of offline work
4. **Self-improve** - learn from evaluation results to optimize offline performance

This creates a **continuous improvement loop** where Sophia becomes increasingly autonomous and capable of high-quality offline operation.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     SOPHIA RUNTIME                           │
│                                                              │
│  ┌──────────────┐        ┌──────────────┐                  │
│  │   ONLINE     │◄──────►│   OFFLINE    │                  │
│  │    MODE      │  Mode  │     MODE     │                  │
│  │              │ Switch │              │                  │
│  │ Cloud LLM    │        │  Local LLM   │                  │
│  │ (DeepSeek)   │        │ (Llama 3.1)  │                  │
│  └──────┬───────┘        └──────┬───────┘                  │
│         │                       │                           │
│         │  Operations           │  Operations               │
│         │  + Signatures         │  + Signatures             │
│         ▼                       ▼                           │
│  ┌──────────────────────────────────────────┐              │
│  │      OPERATION TRACKING SYSTEM            │              │
│  │  (SQLite with model_signature field)     │              │
│  └──────┬─────────────────────┬──────────────┘              │
│         │                     │                             │
│    (online)              (offline)                          │
│         │                     │                             │
│         ▼                     ▼                             │
│  ┌─────────────┐      ┌────────────────┐                   │
│  │ EVALUATION  │      │ CONSOLIDATION  │                   │
│  │   SYSTEM    │      │   (DREAMING)   │                   │
│  │             │      │                │                   │
│  │ Quality     │      │ Memory         │                   │
│  │ Scoring     │      │ Processing     │                   │
│  └─────────────┘      └────────────────┘                   │
│         │                     │                             │
│         └─────────┬───────────┘                             │
│                   ▼                                         │
│         ┌──────────────────┐                                │
│         │  LEARNING LOOP   │                                │
│         │                  │                                │
│         │ Prompt Tuning    │                                │
│         │ Config Adjust    │                                │
│         │ Self-Improvement │                                │
│         └──────────────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementation Components

### 1. Model Signature System

**Purpose:** Track which LLM performed each operation

**Data Structure:**
```python
@dataclass
class OperationMetadata:
    operation_id: str          # UUID for unique operation
    timestamp: str             # ISO format: "2025-11-04T20:52:00Z"
    model_used: str            # "llama3.1:8b" or "openrouter/deepseek/deepseek-chat"
    model_type: str            # "local" or "cloud"
    operation_type: str        # "planning" | "execution" | "consolidation" | "response"
    offline_mode: bool         # True if network unavailable
    success: bool              # Did operation complete successfully
    quality_score: float       # 0.0-1.0 (None until evaluated)
    evaluated_at: str          # ISO timestamp of evaluation (None until evaluated)
    evaluation_model: str      # Model used for evaluation
    prompt_tokens: int         # Token usage
    completion_tokens: int
    total_tokens: int
    latency_ms: float          # Response time
    error_message: str         # If success=False
```

**SQLite Schema Extension:**
```sql
ALTER TABLE conversation_history ADD COLUMN operation_metadata TEXT;
-- Store JSON-serialized OperationMetadata

CREATE TABLE operation_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id TEXT UNIQUE NOT NULL,
    session_id TEXT,
    timestamp TEXT,
    model_used TEXT,
    model_type TEXT,
    operation_type TEXT,
    offline_mode BOOLEAN,
    success BOOLEAN,
    quality_score REAL,
    evaluated_at TEXT,
    evaluation_model TEXT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    latency_ms REAL,
    error_message TEXT,
    raw_metadata TEXT  -- Full JSON for extensibility
);

CREATE INDEX idx_offline_unevaluated ON operation_tracking(offline_mode, quality_score)
    WHERE offline_mode = 1 AND quality_score IS NULL;
```

---

### 2. Offline Mode Implementation

**run.py Changes:**
```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--offline", action="store_true", 
                    help="Force offline mode (local LLM only, no cloud fallback)")
parser.add_argument("--debug", action="store_true",
                    help="Enable debug logging")
args = parser.parse_args()

# Pass to Kernel
kernel = Kernel(offline_mode=args.offline)
```

**core/kernel.py Changes:**
```python
class Kernel:
    def __init__(self, offline_mode: bool = False):
        self.offline_mode = offline_mode
        
    def _select_llm_tool(self) -> Optional[BasePlugin]:
        """Select LLM tool based on mode."""
        if self.offline_mode:
            # Force local LLM only
            llm_tool = self.all_plugins_map.get("tool_local_llm")
            if not llm_tool:
                raise RuntimeError("Offline mode enabled but tool_local_llm not available!")
            logger.info("🔒 OFFLINE MODE: Using local LLM only")
            return llm_tool
        else:
            # Prefer local, fallback to cloud
            llm_tool = self.all_plugins_map.get("tool_local_llm")
            if llm_tool:
                logger.info("🏠 Using local LLM (online mode with local preference)")
            else:
                llm_tool = self.all_plugins_map.get("tool_llm")
                logger.info("☁️ Using cloud LLM (local not available)")
            return llm_tool
```

**plugins/cognitive_planner.py Changes:**
```python
class CognitivePlanner(BasePlugin):
    def setup(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.offline_mode = config.get("offline_mode", False)
        
    def _get_llm_tool(self):
        if self.offline_mode:
            return self.plugins.get("tool_local_llm")
        else:
            return self.plugins.get("tool_local_llm") or self.plugins.get("tool_llm")
```

---

### 3. Memory Consolidation with Model Tracking

**plugins/cognitive_memory_consolidator.py Enhancement:**
```python
class ExtractedMemory(BaseModel):
    # ... existing fields ...
    model_signature: OperationMetadata  # NEW: Track which model extracted this

class ConsolidationResult(BaseModel):
    # ... existing fields ...
    consolidation_model: str  # NEW: Model used for consolidation
    offline_mode: bool        # NEW: Was consolidation done offline
    
async def trigger_consolidation(self, session_ids=None, force=False, offline_mode=False):
    """
    Trigger memory consolidation with model tracking.
    
    Args:
        offline_mode: Force use of local LLM only
    """
    start_time = datetime.now()
    
    # Select LLM based on mode
    if offline_mode:
        llm_tool = self.plugins.get("tool_local_llm")
        model_name = "llama3.1:8b"
    else:
        llm_tool = self.llm_plugin
        model_name = self.llm_model
    
    # Create operation metadata
    operation_metadata = OperationMetadata(
        operation_id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        model_used=model_name,
        model_type="local" if offline_mode else "cloud",
        operation_type="consolidation",
        offline_mode=offline_mode,
        success=False,  # Updated later
        quality_score=None,  # Evaluated later when online
    )
    
    try:
        # ... existing consolidation logic ...
        operation_metadata.success = True
    except Exception as e:
        operation_metadata.success = False
        operation_metadata.error_message = str(e)
    finally:
        # Store operation metadata
        self.sqlite_plugin.save_operation(operation_metadata)
```

---

### 4. Self-Evaluation System

**New Plugin: `plugins/cognitive_self_evaluator.py`**
```python
class CognitiveSelfEvaluator(BasePlugin):
    """
    Evaluates quality of offline operations when back online.
    
    Runs automatically when:
    - Network connection restored
    - Manual trigger via CLI
    - Scheduled daily check
    """
    
    @property
    def name(self) -> str:
        return "cognitive_self_evaluator"
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE
    
    async def evaluate_offline_operations(self) -> EvaluationReport:
        """
        Evaluate all unevaluated offline operations.
        
        Steps:
        1. Query SQLite for offline_mode=True AND quality_score=NULL
        2. For each operation, use cloud LLM to evaluate quality
        3. Store quality scores and improvement suggestions
        4. Generate report with statistics
        """
        # Get unevaluated operations
        operations = self.sqlite_plugin.get_unevaluated_offline_operations()
        
        evaluation_results = []
        for op in operations:
            # Retrieve original context
            context = self.sqlite_plugin.get_operation_context(op.operation_id)
            
            # Use cloud LLM to evaluate
            quality_score = await self._evaluate_operation_quality(
                operation=op,
                context=context,
                evaluator_model="openrouter/deepseek/deepseek-chat"
            )
            
            # Store evaluation
            op.quality_score = quality_score
            op.evaluated_at = datetime.now().isoformat()
            op.evaluation_model = "openrouter/deepseek/deepseek-chat"
            self.sqlite_plugin.update_operation(op)
            
            evaluation_results.append({
                "operation_id": op.operation_id,
                "quality_score": quality_score,
                "model_used": op.model_used,
                "operation_type": op.operation_type
            })
        
        # Generate improvement suggestions
        suggestions = self._generate_improvement_suggestions(evaluation_results)
        
        return EvaluationReport(
            evaluated_count=len(evaluation_results),
            average_quality=sum(r["quality_score"] for r in evaluation_results) / len(evaluation_results),
            suggestions=suggestions
        )
    
    async def _evaluate_operation_quality(self, operation, context, evaluator_model):
        """
        Use cloud LLM to evaluate quality of a single operation.
        
        Evaluation criteria:
        - Correctness (does response match expected output?)
        - Coherence (is response well-structured?)
        - Completeness (does it address all parts of request?)
        - Efficiency (token usage, response time)
        """
        evaluation_prompt = f"""
You are evaluating the quality of an AI operation performed offline.

**Operation Details:**
- Type: {operation.operation_type}
- Model: {operation.model_used}
- Timestamp: {operation.timestamp}
- Success: {operation.success}

**Original Request:**
{context.user_input}

**AI Response:**
{context.llm_response}

**Evaluation Task:**
Rate the quality of this response on a scale of 0.0 to 1.0 based on:
1. **Correctness** (0.4): Is the response factually correct?
2. **Coherence** (0.3): Is the response well-structured and clear?
3. **Completeness** (0.2): Does it address all aspects of the request?
4. **Efficiency** (0.1): Is it concise without unnecessary verbosity?

Return ONLY a JSON object with this structure:
{{
  "quality_score": <float 0.0-1.0>,
  "correctness": <float 0.0-1.0>,
  "coherence": <float 0.0-1.0>,
  "completeness": <float 0.0-1.0>,
  "efficiency": <float 0.0-1.0>,
  "issues": ["<issue 1>", "<issue 2>", ...],
  "suggestions": ["<suggestion 1>", "<suggestion 2>", ...]
}}
"""
        
        # Call cloud LLM for evaluation
        response = await self.cloud_llm_tool.generate(
            prompt=evaluation_prompt,
            model=evaluator_model,
            temperature=0.1,  # Low temperature for consistent evaluation
            max_tokens=1000
        )
        
        # Parse JSON response
        import json
        evaluation = json.loads(response)
        
        return evaluation["quality_score"]
    
    def _generate_improvement_suggestions(self, evaluation_results):
        """
        Analyze evaluation results to generate improvement suggestions.
        
        Returns:
        - Prompt adjustments for local LLM
        - Configuration changes
        - Model selection recommendations
        """
        avg_quality = sum(r["quality_score"] for r in evaluation_results) / len(evaluation_results)
        
        suggestions = []
        
        if avg_quality < 0.6:
            suggestions.append({
                "priority": "HIGH",
                "type": "model_change",
                "message": "Consider using larger local model (e.g., Llama 3.1 70B) for better quality"
            })
        
        if avg_quality < 0.7:
            suggestions.append({
                "priority": "MEDIUM",
                "type": "prompt_tuning",
                "message": "Tune prompts for local LLM - add more context and examples"
            })
        
        # Analyze by operation type
        planning_ops = [r for r in evaluation_results if r["operation_type"] == "planning"]
        if planning_ops:
            avg_planning_quality = sum(r["quality_score"] for r in planning_ops) / len(planning_ops)
            if avg_planning_quality < 0.65:
                suggestions.append({
                    "priority": "HIGH",
                    "type": "planning_improvement",
                    "message": "Planning quality low - consider reverting to cloud LLM for planning tasks"
                })
        
        return suggestions
```

---

### 5. Sleep Scheduler Integration

**plugins/core_sleep_scheduler.py Enhancement:**
```python
async def _run_consolidation_cycle(self):
    """
    Run memory consolidation during sleep cycle.
    
    Enhancement: Force offline mode during scheduled sleep.
    """
    logger.info("🌙 Entering sleep cycle - switching to OFFLINE mode")
    
    # Trigger consolidation in offline mode
    result = await self.consolidator_plugin.trigger_consolidation(
        session_ids=None,  # All unconsolidated sessions
        force=False,
        offline_mode=True  # NEW: Force offline
    )
    
    logger.info(f"🌙 Sleep cycle complete: {result.memories_created} memories created (OFFLINE)")
    
    # Emit DREAM_COMPLETED event
    if self.event_bus:
        self.event_bus.publish(Event(
            event_type=EventType.DREAM_COMPLETED,
            source=self.name,
            data={
                "memories_created": result.memories_created,
                "offline_mode": True,  # NEW
                "model_used": "llama3.1:8b"  # NEW
            }
        ))
```

---

## 🧪 Testing Strategy

### Test 1: Offline Mode Basic Functionality
```bash
# Disconnect network
sudo ip link set eth0 down

# Run Sophia in offline mode
python run.py --offline --once "Co je to AGI?"

# Check operation tracking
sqlite3 data/memory/sophia_memory.db "
SELECT operation_id, model_used, offline_mode, success 
FROM operation_tracking 
ORDER BY timestamp DESC 
LIMIT 1;
"

# Reconnect network
sudo ip link set eth0 up
```

**Expected:**
- ✅ Sophia responds using Llama 3.1 8B
- ✅ `offline_mode=1` in database
- ✅ `model_used="llama3.1:8b"`
- ✅ `success=1`

---

### Test 2: Sleep Cycle with Offline Consolidation
```bash
# Manually trigger sleep cycle
python -c "
import asyncio
from core.kernel import Kernel

async def test_sleep():
    k = Kernel()
    await k.initialize()
    
    # Get sleep scheduler
    scheduler = k.all_plugins_map.get('core_sleep_scheduler')
    
    # Trigger manual sleep cycle
    await scheduler.trigger_consolidation('manual')

asyncio.run(test_sleep())
"

# Check consolidation results
sqlite3 data/memory/sophia_memory.db "
SELECT COUNT(*) as offline_consolidations
FROM operation_tracking 
WHERE operation_type='consolidation' 
  AND offline_mode=1;
"
```

**Expected:**
- ✅ Consolidation runs using local LLM
- ✅ New memories created with model signatures
- ✅ All tracked in SQLite

---

### Test 3: Self-Evaluation Loop
```bash
# Step 1: Create offline operations (network disconnected)
sudo ip link set eth0 down
python run.py --offline --once "Kdo je Sophia?"
python run.py --offline --once "Kolik je 5+7?"
sudo ip link set eth0 up

# Step 2: Run evaluation when back online
python -c "
import asyncio
from core.kernel import Kernel

async def test_eval():
    k = Kernel()
    await k.initialize()
    
    # Get self-evaluator
    evaluator = k.all_plugins_map.get('cognitive_self_evaluator')
    
    # Run evaluation
    report = await evaluator.evaluate_offline_operations()
    
    print(f'Evaluated: {report.evaluated_count} operations')
    print(f'Avg Quality: {report.average_quality:.2f}')
    print(f'Suggestions: {len(report.suggestions)}')
    
    for s in report.suggestions:
        print(f'  [{s[\"priority\"]}] {s[\"message\"]}')

asyncio.run(test_eval())
"

# Check updated quality scores
sqlite3 data/memory/sophia_memory.db "
SELECT operation_id, model_used, quality_score, evaluated_at
FROM operation_tracking 
WHERE offline_mode=1 
  AND quality_score IS NOT NULL
ORDER BY timestamp DESC;
"
```

**Expected:**
- ✅ 2 operations evaluated
- ✅ Quality scores stored (0.0-1.0)
- ✅ Improvement suggestions generated
- ✅ `evaluated_at` timestamps set

---

### Test 4: Benchmark Local Models
```bash
# Use existing tool_model_evaluator
python -c "
import asyncio
from plugins.tool_model_evaluator import ModelEvaluator

async def benchmark():
    evaluator = ModelEvaluator()
    
    # Test Llama 3.1 8B
    result_llama = await evaluator.benchmark_model(
        model_name='llama3.1:8b',
        provider='ollama',
        test_suite='function_calling'
    )
    
    # Test Gemma 2B
    result_gemma = await evaluator.benchmark_model(
        model_name='gemma2:2b',
        provider='ollama',
        test_suite='function_calling'
    )
    
    # Compare
    print(f'Llama 3.1 8B: {result_llama.success_rate:.1%}')
    print(f'Gemma 2B: {result_gemma.success_rate:.1%}')
    
    # Save results
    evaluator.save_results('docs/benchmarks/offline_models.json')

asyncio.run(benchmark())
"
```

**Expected:**
- ✅ Llama 3.1 8B: >80% success rate on function calling
- ✅ Gemma 2B: <50% success rate (too small)
- ✅ Results saved to benchmarks/

---

## 📊 Metrics & Monitoring

### Dashboard View (Future WebUI Enhancement)
```
╔══════════════════════════════════════════════════════════════╗
║           SOPHIA OFFLINE PERFORMANCE DASHBOARD                ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📊 OPERATION STATISTICS (Last 7 Days)                       ║
║  ┌────────────────────────────────────────────────────┐     ║
║  │ Total Operations:        1,247                     │     ║
║  │ Offline Operations:        342 (27.4%)            │     ║
║  │ Online Operations:         905 (72.6%)            │     ║
║  │ Evaluated Offline Ops:     310 (90.6%)            │     ║
║  └────────────────────────────────────────────────────┘     ║
║                                                              ║
║  🎯 QUALITY SCORES                                           ║
║  ┌────────────────────────────────────────────────────┐     ║
║  │ Offline Avg Quality:     0.78  [████████░░] 78%    │     ║
║  │ Online Avg Quality:      0.92  [█████████░] 92%    │     ║
║  │ Gap:                    -0.14  (Improvement: +0.03)│     ║
║  └────────────────────────────────────────────────────┘     ║
║                                                              ║
║  🤖 MODEL USAGE                                              ║
║  ┌────────────────────────────────────────────────────┐     ║
║  │ Llama 3.1 8B:     342 ops  (Quality: 0.78)         │     ║
║  │ DeepSeek Chat:    905 ops  (Quality: 0.92)         │     ║
║  └────────────────────────────────────────────────────┘     ║
║                                                              ║
║  💡 IMPROVEMENT SUGGESTIONS                                  ║
║  ┌────────────────────────────────────────────────────┐     ║
║  │ [HIGH] Tune prompts for local LLM planning tasks   │     ║
║  │ [MED]  Increase temperature for creative responses │     ║
║  └────────────────────────────────────────────────────┘     ║
║                                                              ║
║  🌙 LAST DREAM CYCLE                                         ║
║  ┌────────────────────────────────────────────────────┐     ║
║  │ Time:         2025-11-04 23:15:00                  │     ║
║  │ Sessions:     12 processed                         │     ║
║  │ Memories:     34 created                           │     ║
║  │ Model:        llama3.1:8b (offline)                │     ║
║  │ Quality:      0.81  [████████░░] 81%               │     ║
║  └────────────────────────────────────────────────────┘     ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 🚀 Deployment Plan

### Phase 1: Foundation (Today)
- [x] Design architecture ✅ YOU ARE HERE
- [ ] Extend SQLite schema with operation_tracking table
- [ ] Implement OperationMetadata tracking in kernel
- [ ] Add --offline flag to run.py
- [ ] Test basic offline mode

### Phase 2: Model Tracking (Tomorrow)
- [ ] Enhance cognitive_memory_consolidator with model signatures
- [ ] Update core_sleep_scheduler for offline consolidation
- [ ] Test sleep cycle with offline mode
- [ ] Verify signatures stored correctly

### Phase 3: Self-Evaluation (Day 3)
- [ ] Create cognitive_self_evaluator plugin
- [ ] Implement quality scoring algorithm
- [ ] Generate improvement suggestions
- [ ] Test evaluation loop end-to-end

### Phase 4: Optimization (Day 4-5)
- [ ] Benchmark Llama 3.1 8B with tool_model_evaluator
- [ ] Tune prompts for local LLM based on evaluation results
- [ ] Adjust configuration (temperature, max_tokens)
- [ ] Re-run benchmarks and compare

### Phase 5: Documentation & Polish (Day 6-7)
- [ ] Create WebUI dashboard mockup
- [ ] Write user guide for offline mode
- [ ] Add CLI commands for manual evaluation
- [ ] Create demo video

---

## 🎓 Example Usage

### Scenario: Weekend Offline Work

**Friday Evening (Before going offline):**
```bash
# Run normal online operation
python run.py --once "Připrav mi seznam úkolů na víkend"
# Uses: OpenRouter / DeepSeek Chat
```

**Saturday Morning (Offline at cottage):**
```bash
# Enable offline mode
python run.py --offline --once "Co jsou nejdůležitější úkoly z toho seznamu?"
# Uses: Llama 3.1 8B (local)
# Stores: operation_metadata with offline_mode=True
```

**Sunday Night (Back online):**
```bash
# Automatic evaluation triggers when online
# OR manually trigger:
python scripts/evaluate_offline_work.py

# Output:
# 🔍 Evaluating 15 offline operations...
# ✅ Average quality: 0.76
# 💡 Suggestions:
#    [HIGH] Improve planning prompts for local LLM
#    [MED]  Increase context window for complex tasks
```

**Monday Morning (Apply improvements):**
```bash
# Sophia automatically tunes prompts based on Sunday evaluation
# Next offline session will have better quality
```

---

## 🔮 Future Enhancements

### Advanced Self-Improvement
- **Automatic Prompt Engineering:** Use evaluation results to auto-generate better prompts
- **Dynamic Model Selection:** Choose Llama 70B for complex tasks, Gemma 2B for simple ones
- **Federated Learning:** Share anonymized improvement data with other Sophia instances
- **Meta-Learning:** Learn which types of tasks work best offline vs online

### Enhanced Dreaming
- **Active Dreaming:** Generate synthetic questions during sleep to fill knowledge gaps
- **Counterfactual Reasoning:** "What if I had used cloud LLM for that offline task?"
- **Memory Pruning:** Delete low-quality offline memories, keep only high-quality ones

### Multi-Model Ensemble
- **Consensus Voting:** Run same task on 3 local models, use majority vote
- **Hybrid Execution:** Start with local LLM, escalate to cloud if confidence low
- **Model Specialization:** Different models for different tasks (coding, creative, factual)

---

## 📚 References

- **Sophia AGI Documentation:** `docs/en/AGENTS.md`
- **Sleep Scheduler:** `plugins/core_sleep_scheduler.py`
- **Memory Consolidator:** `plugins/cognitive_memory_consolidator.py`
- **Model Evaluator:** `plugins/tool_model_evaluator.py`
- **Ollama Documentation:** https://ollama.com/library/llama3.1
- **Pydantic Models:** https://docs.pydantic.dev/

---

## ✅ Success Criteria

Sophia's offline dreaming system is successful when:

1. **Autonomy:** Sophia runs fully offline for 24+ hours without errors
2. **Quality:** Offline operation quality >75% compared to online
3. **Self-Awareness:** Sophia knows when she performed well/poorly offline
4. **Improvement:** Quality gap decreases by 10% per week through self-learning
5. **Transparency:** Users can see which model generated each response
6. **Efficiency:** Offline operations use <50% tokens compared to cloud

---

**Last Updated:** 2025-11-04  
**Next Review:** After Phase 1 completion

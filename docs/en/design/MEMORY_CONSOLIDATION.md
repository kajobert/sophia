# Memory Consolidation & Dreaming - Design Specification

**Version:** 1.0  
**Date:** 2025-11-03  
**Status:** Design Specification  
**Phase:** 3 - Memory Consolidation & Dreaming  
**Author:** Sophia AI Agent

---

## 📋 Overview

The Memory Consolidation system enables Sophia to autonomously process and distill experiences from conversation sessions into structured, long-term knowledge. This is analogous to human "dreaming" - converting short-term episodic memories into long-term semantic knowledge.

### **Goals**
1. ✅ Autonomous memory processing - no human intervention required
2. ✅ Knowledge extraction - identify key insights, patterns, learnings
3. ✅ Noise reduction - remove conversational fluff
4. ✅ Smart retrieval - relevance + recency based search
5. ✅ Scheduled consolidation - "sleep cycles" during low activity

---

## 🎯 Core Concepts

### **Memory Types**

```python
from enum import Enum

class MemoryType(Enum):
    """Types of memories in Sophia's knowledge base."""
    
    # Raw memories (unconsolidated)
    RAW_CONVERSATION = "raw_conversation"      # Full conversation transcript
    RAW_SESSION = "raw_session"                # Session metadata
    
    # Consolidated memories (processed)
    INSIGHT = "insight"                        # Key learning or discovery
    PATTERN = "pattern"                        # Recurring behavior or pattern
    FACT = "fact"                              # Concrete factual knowledge
    PROCEDURE = "procedure"                    # How to do something
    DECISION = "decision"                      # Decision made and rationale
    ERROR_LESSON = "error_lesson"              # Mistake and how to avoid it
    
    # Meta-memories
    CONSOLIDATION_SUMMARY = "consolidation_summary"  # Summary of consolidation session

class ImportanceLevel(Enum):
    """Importance levels for memory prioritization."""
    CRITICAL = 5    # Must never forget
    HIGH = 4        # Very important
    NORMAL = 3      # Standard importance
    LOW = 2         # Nice to know
    TRIVIAL = 1     # Can be forgotten
```

### **Memory Consolidation Process**

```
┌─────────────────────────────────────────────────────────────┐
│                   SLEEP CYCLE TRIGGERED                     │
│        (every 6 hours OR low-activity detection)            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: Gather Raw Memories                               │
│  • Query SQLite for unconsolidated sessions                 │
│  • Load conversation history                                │
│  • Filter out already consolidated                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: LLM Analysis                                      │
│  • Send conversation to LLM with extraction prompt          │
│  • Extract: insights, patterns, facts, procedures           │
│  • Assign importance scores                                 │
│  • Generate concise summaries                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: Deduplication                                     │
│  • Search ChromaDB for similar memories                     │
│  • Merge duplicates or strengthen existing                  │
│  • Update importance scores based on repetition             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 4: Storage                                           │
│  • Store consolidated memories in ChromaDB                  │
│  • Mark raw sessions as "consolidated" in SQLite            │
│  • Emit DREAM_COMPLETED event with metrics                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧠 Memory Consolidation Plugin

### **Plugin Structure**

```python
class CognitiveMemoryConsolidator(BasePlugin):
    """
    Cognitive Memory Consolidator Plugin
    
    Autonomously processes conversation sessions to extract and store
    long-term knowledge. Runs during "sleep cycles" to minimize
    interference with active tasks.
    
    Tool Definitions:
    - trigger_memory_consolidation: Manually trigger consolidation
    - get_consolidation_status: Check consolidation metrics
    - search_consolidated_memories: Search knowledge base
    """
```

### **LLM Extraction Prompt**

```python
CONSOLIDATION_PROMPT = """
You are Sophia's memory consolidation system. Analyze the following conversation
and extract key knowledge that should be permanently stored.

CONVERSATION:
{conversation_history}

Extract the following:

1. INSIGHTS (key learnings, discoveries, realizations):
   - What did Sophia learn?
   - What worked well?
   - What surprised Sophia?

2. PATTERNS (recurring behaviors, tendencies):
   - What patterns emerged?
   - What does the user prefer?
   - What approaches are effective?

3. FACTS (concrete, verifiable information):
   - What factual knowledge was gained?
   - What are the user's preferences/constraints?

4. PROCEDURES (how to do things):
   - What workflows were successful?
   - What are the steps for common tasks?

5. ERRORS & LESSONS (mistakes and how to avoid them):
   - What went wrong?
   - How can it be prevented?

For each item:
- Provide concise summary (1-2 sentences)
- Assign importance (1-5)
- Tag with relevant keywords

Return as JSON:
{
    "insights": [...],
    "patterns": [...],
    "facts": [...],
    "procedures": [...],
    "error_lessons": [...]
}
"""
```

---

## 📅 Sleep Cycle Scheduler

### **Triggers**

```python
class SleepCycleTrigger(Enum):
    """When to trigger memory consolidation."""
    TIME_BASED = "time_based"          # Every N hours
    LOW_ACTIVITY = "low_activity"      # No user input for N minutes
    SESSION_END = "session_end"        # When session ends
    MANUAL = "manual"                  # Manually triggered
```

### **Configuration**

```yaml
# config/autonomy.yaml
memory_consolidation:
  enabled: true
  schedule:
    type: "time_based"  # or "low_activity"
    interval_hours: 6   # Consolidate every 6 hours
    idle_minutes: 30    # Or after 30 minutes of inactivity
  
  llm_config:
    model: "gemini-2.0-flash-thinking-exp-1219"  # Fast, cheap model for consolidation
    max_tokens: 4000
    temperature: 0.3
  
  storage:
    min_importance: 2    # Don't store memories with importance < 2
    max_age_days: 90     # Archive memories older than 90 days
    dedup_threshold: 0.85  # Similarity threshold for deduplication
```

---

## 🔌 Enhanced ChromaDB Plugin

### **Metadata Structure**

```python
# Enhanced metadata for memories
{
    "memory_id": "mem_abc123",
    "memory_type": "insight",
    "importance": 4,
    "session_id": "sess_xyz789",
    "created_at": "2025-11-03T12:00:00Z",
    "consolidated_at": "2025-11-03T18:00:00Z",
    "source_type": "conversation",
    "keywords": ["python", "testing", "async"],
    "user_id": "robert",
    "access_count": 0,
    "last_accessed": null,
    "consolidation_count": 1  # How many times reinforced
}
```

### **Smart Retrieval**

```python
def search_memories(
    query: str,
    memory_types: Optional[List[MemoryType]] = None,
    min_importance: int = 2,
    recency_weight: float = 0.3,  # 30% weight for recency
    limit: int = 5
) -> List[Memory]:
    """
    Search memories with relevance + recency scoring.
    
    Score = (relevance * (1 - recency_weight)) + (recency * recency_weight)
    """
```

---

## 📡 Event Emissions

```python
# Dream cycle started
Event(
    event_type=EventType.DREAM_STARTED,
    source="cognitive_memory_consolidator",
    priority=EventPriority.LOW,  # Low priority - background task
    data={
        "session_count": 5,
        "estimated_duration": 30
    }
)

# Dream cycle completed
Event(
    event_type=EventType.DREAM_COMPLETED,
    source="cognitive_memory_consolidator",
    priority=EventPriority.NORMAL,
    data={
        "sessions_processed": 5,
        "memories_created": 23,
        "memories_merged": 7,
        "duration": 28.5,
        "metrics": {
            "insights": 8,
            "patterns": 5,
            "facts": 6,
            "procedures": 3,
            "error_lessons": 1
        }
    }
)
```

---

## ✅ Implementation Checklist

**Phase 3.1: Memory Consolidator Plugin (Day 1-2)**
- [ ] Create `plugins/cognitive_memory_consolidator.py`
- [ ] Implement memory extraction prompt
- [ ] Implement LLM-based analysis
- [ ] Implement deduplication logic
- [ ] Add tool definitions
- [ ] Write unit tests

**Phase 3.2: Sleep Cycle Scheduler (Day 2-3)**
- [ ] Implement time-based trigger
- [ ] Implement low-activity detection
- [ ] Add configuration loading
- [ ] Integrate with Event Loop
- [ ] Add metrics tracking

**Phase 3.3: ChromaDB Enhancement (Day 3)**
- [ ] Update `memory_chroma.py` with metadata
- [ ] Implement smart retrieval (relevance + recency)
- [ ] Add deduplication support
- [ ] Add archival support

**Phase 3.4: E2E Testing (Day 4)**
- [ ] Test full consolidation cycle
- [ ] Test deduplication
- [ ] Test smart retrieval
- [ ] Test sleep cycle triggering

---

## 🎯 Success Criteria

1. ✅ Consolidation runs automatically every 6 hours
2. ✅ Memories are extracted and categorized correctly
3. ✅ Duplicate memories are detected and merged
4. ✅ Smart retrieval returns relevant + recent memories
5. ✅ Events are emitted on dream start/completion
6. ✅ All tests pass (>90% coverage)
7. ✅ Consolidation doesn't interfere with active tasks

---

## 📚 Related Documents

- `docs/en/AUTONOMOUS_MVP_ROADMAP.md` - Overall roadmap
- `docs/en/design/EVENT_SYSTEM.md` - Event architecture
- `plugins/memory_chroma.py` - Existing ChromaDB plugin
- `plugins/memory_sqlite.py` - Existing SQLite plugin

---

**Status:** Ready for Implementation  
**Estimated Time:** 3-4 days  
**Priority:** MEDIUM

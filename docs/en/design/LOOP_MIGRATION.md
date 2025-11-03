# Loop Migration Strategy

**Version:** 1.0  
**Date:** 2025-11-03  
**Status:** Design Specification  
**Phase:** 1 - Continuous Loop  
**Author:** Sophia AI Agent

---

## 📋 Overview

This document outlines the step-by-step migration strategy to transform Sophia's current blocking consciousness loop into an event-driven, non-blocking architecture. The migration follows a **gradual, backwards-compatible approach** to minimize risk and ensure stability.

### **Current State (Blocking)**
```python
# Simplified version of current kernel.py
async def consciousness_loop(self):
    while self.context.running:
        # Get user input (BLOCKS until input received)
        user_input = input("You: ")
        
        # Process input (BLOCKS during processing)
        response = await self.process_input(user_input)
        
        # Display response
        print(f"Sophia: {response}")
        
        # Can't do anything else while waiting for input or processing
```

### **Target State (Event-Driven)**
```python
# Event-driven consciousness loop
async def consciousness_loop(self):
    while self.context.running:
        # Check for user input (NON-BLOCKING)
        if input_available():
            user_input = get_input()
            self.event_bus.publish(Event(USER_INPUT, data={"input": user_input}))
        
        # Process events continuously (NON-BLOCKING)
        # Tasks run in background via TaskQueue
        
        # Small sleep to prevent CPU spinning
        await asyncio.sleep(0.01)
```

---

## 🎯 Migration Goals

### **Primary Objectives**
1. ✅ **Non-blocking operation** - Chat while executing tasks
2. ✅ **Backwards compatibility** - No breaking changes to plugins
3. ✅ **Zero downtime** - Gradual rollout, feature flags
4. ✅ **Testability** - Comprehensive tests at each step
5. ✅ **Rollback capability** - Can revert if issues arise

### **Success Criteria**
- Sophia can respond to user input while executing background tasks
- Existing plugins continue to work without modification
- No performance regression (<5% overhead acceptable)
- All tests pass
- Documentation updated

---

## 🗺️ Migration Phases

### **Phase 1: Foundation (Days 1-2)**
**Goal:** Set up event system and task queue without disrupting existing functionality.

#### **Step 1.1: Create Event Infrastructure**
```bash
# New files to create
core/events.py          # Event, EventType, EventPriority classes
core/event_bus.py       # EventBus implementation
tests/core/test_event_bus.py
```

**Tasks:**
- [ ] Implement `Event` dataclass with validation
- [ ] Implement `EventBus` with pub/sub pattern
- [ ] Write unit tests (>90% coverage)
- [ ] Add to `SharedContext` as optional field

**Validation:**
```python
# Test that event bus works standalone
async def test_event_bus():
    bus = EventBus()
    await bus.start()
    
    received = []
    bus.subscribe(EventType.CUSTOM, lambda e: received.append(e))
    bus.publish(Event(event_type=EventType.CUSTOM))
    
    await asyncio.sleep(0.1)
    assert len(received) == 1
    
    await bus.stop()
```

#### **Step 1.2: Create Task Queue Infrastructure**
```bash
# New files to create
core/task.py            # Task, TaskStatus, TaskPriority classes
core/task_queue.py      # TaskQueue implementation
tests/core/test_task_queue.py
```

**Tasks:**
- [ ] Implement `Task` dataclass
- [ ] Implement `TaskQueue` with priority queues
- [ ] Wire up with `EventBus`
- [ ] Write unit tests (>90% coverage)
- [ ] Add to `SharedContext` as optional field

**Validation:**
```python
# Test that task queue works standalone
async def test_task_queue():
    bus = EventBus()
    await bus.start()
    
    queue = TaskQueue(bus)
    await queue.start()
    
    async def test_task():
        return "success"
    
    task = Task(name="test", function=test_task)
    result = await queue.add_task(task, wait_for_completion=True)
    
    assert result.success
    
    await queue.stop()
    await bus.stop()
```

#### **Step 1.3: Update SharedContext**
```python
# core/context.py

@dataclass
class SharedContext:
    # Existing fields...
    mode: str
    verbose: bool
    plugins: Dict[str, Any]
    
    # NEW: Event-driven components (optional for backwards compat)
    event_bus: Optional[EventBus] = None
    task_queue: Optional[TaskQueue] = None
    
    # Feature flag to enable new architecture
    use_event_driven: bool = False
```

**Tasks:**
- [ ] Add optional event bus field
- [ ] Add optional task queue field
- [ ] Add feature flag `use_event_driven`
- [ ] Update documentation

---

### **Phase 2: Parallel Run (Days 3-4)**
**Goal:** Run event system alongside existing blocking code. No behavioral changes yet.

#### **Step 2.1: Initialize Event System in Kernel**
```python
# core/kernel.py

class Kernel:
    def __init__(self, mode="terminal", use_event_driven=False):
        # ... existing init ...
        
        # NEW: Event-driven components (if enabled)
        if use_event_driven:
            self.event_bus = EventBus()
            self.task_queue = TaskQueue(self.event_bus)
            
            # Add to context
            self.context.event_bus = self.event_bus
            self.context.task_queue = self.task_queue
            self.context.use_event_driven = True
        else:
            self.event_bus = None
            self.task_queue = None
    
    async def startup(self):
        # ... existing startup ...
        
        # NEW: Start event system
        if self.context.use_event_driven:
            await self.event_bus.start()
            await self.task_queue.start()
            
            # Publish startup event
            self.event_bus.publish(Event(
                event_type=EventType.SYSTEM_STARTUP,
                source="kernel"
            ))
    
    async def shutdown(self):
        # NEW: Stop event system
        if self.context.use_event_driven:
            await self.task_queue.stop()
            await self.event_bus.stop()
        
        # ... existing shutdown ...
```

**Tasks:**
- [ ] Add initialization in `Kernel.__init__`
- [ ] Start event bus/queue in `startup()`
- [ ] Stop in `shutdown()`
- [ ] Add logging for diagnostics
- [ ] Test with `use_event_driven=True`

**Validation:**
```bash
# Run Sophia with event system enabled (should work same as before)
python run.py --mode terminal --use-event-driven

# Check logs for event system startup
# Should see: "EventBus started", "TaskQueue started"
```

#### **Step 2.2: Emit Events Without Acting On Them**
```python
# core/kernel.py

async def consciousness_loop(self):
    """Main loop - emit events but still use blocking code"""
    while self.context.running:
        # Get user input (STILL BLOCKING)
        user_input = input("You: ")
        
        # NEW: Emit event (parallel to existing flow)
        if self.context.use_event_driven:
            self.event_bus.publish(Event(
                event_type=EventType.USER_INPUT,
                source="kernel",
                priority=EventPriority.HIGH,
                data={"input": user_input}
            ))
        
        # Process input (STILL BLOCKING - existing code unchanged)
        response = await self.process_input(user_input)
        
        # Display response
        print(f"Sophia: {response}")
```

**Tasks:**
- [ ] Emit `USER_INPUT` events
- [ ] Emit `TASK_CREATED` events from planner
- [ ] Emit `TASK_COMPLETED` events
- [ ] Log events for verification
- [ ] **Don't change existing behavior**

**Validation:**
```python
# Check that events are being emitted
def test_events_emitted():
    # Subscribe to USER_INPUT
    events = []
    kernel.event_bus.subscribe(EventType.USER_INPUT, lambda e: events.append(e))
    
    # Simulate user input
    # ... 
    
    # Verify event was published
    assert len(events) == 1
    assert events[0].data["input"] == "test input"
```

---

### **Phase 3: Gradual Cutover (Days 5-6)**
**Goal:** Start using events for actual behavior, plugin by plugin.

#### **Step 3.1: Migrate Planner to Events**

**Current:** Planner is called directly from kernel

```python
# OLD: Direct call
plan = await self.planner.create_plan(user_input)
```

**New:** Planner subscribes to USER_INPUT event

```python
# plugins/cognitive_planner.py

class CognitivePlanner(BasePlugin):
    def on_load(self, context: SharedContext):
        # ... existing init ...
        
        # NEW: Subscribe to USER_INPUT events
        if context.use_event_driven:
            context.event_bus.subscribe(EventType.USER_INPUT, self._handle_user_input)
    
    async def _handle_user_input(self, event: Event):
        """Handle USER_INPUT event"""
        user_input = event.data["input"]
        
        # Create plan
        plan = await self.create_plan(user_input)
        
        # Convert plan to tasks
        for step in plan.steps:
            task = self._step_to_task(step)
            
            # Publish TASK_CREATED event
            self.context.event_bus.publish(Event(
                event_type=EventType.TASK_CREATED,
                source="cognitive_planner",
                priority=EventPriority.NORMAL,
                data=task.__dict__
            ))
```

**Tasks:**
- [ ] Add event subscription in planner
- [ ] Emit TASK_CREATED events
- [ ] Keep old direct-call path for backwards compat
- [ ] Use feature flag to switch between old/new
- [ ] Test both paths

#### **Step 3.2: Migrate TaskQueue to Execute Tasks**

**Current:** Tasks executed directly in kernel

**New:** TaskQueue subscribes to TASK_CREATED and executes

```python
# core/task_queue.py (already has this in design)

async def _handle_task_created(self, event: Event):
    """Handle TASK_CREATED event"""
    task_data = event.data
    
    # Create task object
    task = Task(**task_data)
    
    # Add to queue (starts execution)
    await self.add_task(task)
```

**Tasks:**
- [ ] Subscribe to TASK_CREATED in TaskQueue
- [ ] Execute tasks asynchronously
- [ ] Emit TASK_COMPLETED events
- [ ] Keep old direct execution for backwards compat

#### **Step 3.3: Update Kernel Loop to be Non-Blocking**

```python
# core/kernel.py

async def consciousness_loop(self):
    """Main loop - now non-blocking"""
    
    # Only use new loop if feature enabled
    if self.context.use_event_driven:
        await self._event_driven_loop()
    else:
        await self._blocking_loop()  # Old behavior

async def _event_driven_loop(self):
    """NEW: Event-driven consciousness loop"""
    while self.context.running:
        # Check for user input (NON-BLOCKING)
        user_input = await self._get_user_input_nonblocking()
        
        if user_input:
            # Publish event
            self.event_bus.publish(Event(
                event_type=EventType.USER_INPUT,
                source="kernel",
                priority=EventPriority.HIGH,
                data={"input": user_input}
            ))
        
        # Small sleep to prevent CPU spinning
        await asyncio.sleep(0.01)

async def _blocking_loop(self):
    """OLD: Blocking consciousness loop (kept for backwards compat)"""
    # ... existing blocking code ...

async def _get_user_input_nonblocking(self) -> Optional[str]:
    """Get user input without blocking"""
    # Implementation depends on interface (terminal vs webui)
    
    if self.context.mode == "terminal":
        # Use asyncio to check stdin without blocking
        import sys
        import select
        
        # Check if input is available
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline()
            return line.strip() if line else None
        return None
    
    elif self.context.mode == "webui":
        # WebUI uses WebSocket - already non-blocking
        # Check message queue
        return await self._webui_get_message()
    
    return None
```

**Tasks:**
- [ ] Implement non-blocking input reading
- [ ] Create new event-driven loop
- [ ] Keep old blocking loop
- [ ] Feature flag to switch
- [ ] Test both modes

---

### **Phase 4: Plugin Migration (Day 7)**
**Goal:** Migrate plugins to use events where beneficial.

#### **High-Priority Plugins to Migrate:**

1. **Jules Monitor** (`cognitive_jules_monitor.py`)
   - Subscribe to JULES_TASK_STARTED
   - Publish JULES_TASK_COMPLETED

2. **Memory** (`memory_sqlite.py`, `memory_chroma.py`)
   - Subscribe to TASK_COMPLETED
   - Store results automatically

3. **UI** (`interface_terminal.py`, `interface_webui.py`)
   - Subscribe to TASK_STARTED, TASK_PROGRESS, TASK_COMPLETED
   - Update UI in real-time

4. **Logging Manager** (`core_logging_manager.py`)
   - Subscribe to all events
   - Log for debugging

**Migration Template:**
```python
# plugins/example_plugin.py

class ExamplePlugin(BasePlugin):
    def on_load(self, context: SharedContext):
        # ... existing init ...
        
        # NEW: Subscribe to events if enabled
        if context.use_event_driven:
            self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Subscribe to relevant events"""
        self.context.event_bus.subscribe(
            EventType.TASK_COMPLETED,
            self._handle_task_completed
        )
    
    async def _handle_task_completed(self, event: Event):
        """Handle task completion"""
        task_id = event.data["task_id"]
        result = event.data["result"]
        
        # Process result...
```

**Tasks:**
- [ ] Migrate 4 high-priority plugins
- [ ] Test each plugin migration
- [ ] Update plugin documentation
- [ ] Create migration guide for other plugins

---

### **Phase 5: Enable by Default (Day 8)**
**Goal:** Make event-driven the default, but keep blocking as fallback.

```python
# core/kernel.py

class Kernel:
    def __init__(self, mode="terminal", use_event_driven=True):  # Changed default!
        # ...
```

```python
# run.py

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="terminal")
    parser.add_argument("--use-blocking", action="store_true",
                       help="Use old blocking loop (fallback)")
    args = parser.parse_args()
    
    kernel = Kernel(
        mode=args.mode,
        use_event_driven=not args.use_blocking  # Event-driven by default
    )
```

**Tasks:**
- [ ] Change default to `use_event_driven=True`
- [ ] Add CLI flag to revert to blocking
- [ ] Update documentation
- [ ] Run full benchmark suite
- [ ] Monitor for issues

**Validation:**
```bash
# Default run uses event-driven
python run.py

# Can still use blocking if needed
python run.py --use-blocking
```

---

### **Phase 6: Cleanup (Days 9-10)**
**Goal:** Remove blocking code after stability is confirmed.

**After 1-2 weeks of stable operation:**

```python
# core/kernel.py

# REMOVE old blocking loop
async def _blocking_loop(self):
    # DELETE THIS METHOD

# REMOVE feature flag
class Kernel:
    def __init__(self, mode="terminal"):  # Remove use_event_driven parameter
        # Always use event-driven
```

**Tasks:**
- [ ] Remove `use_event_driven` flag
- [ ] Remove old blocking code
- [ ] Remove backwards compat checks
- [ ] Update all documentation
- [ ] Final benchmark run
- [ ] Tag release `v2.0.0-event-driven`

---

## 🧪 Testing Strategy

### **Unit Tests** (Each Phase)
```python
# tests/core/test_migration.py

@pytest.mark.asyncio
async def test_backwards_compatibility():
    """Ensure old blocking mode still works"""
    kernel = Kernel(use_event_driven=False)
    await kernel.startup()
    
    # Should work exactly as before
    # ... test existing functionality ...
    
    await kernel.shutdown()

@pytest.mark.asyncio
async def test_event_driven_mode():
    """Ensure new event-driven mode works"""
    kernel = Kernel(use_event_driven=True)
    await kernel.startup()
    
    # Should handle events
    # ... test event flow ...
    
    await kernel.shutdown()

@pytest.mark.asyncio
async def test_concurrent_execution():
    """Ensure tasks can run concurrently"""
    kernel = Kernel(use_event_driven=True)
    await kernel.startup()
    
    # Start long-running task
    kernel.task_queue.add_task(long_task)
    
    # Should still accept user input
    kernel.event_bus.publish(Event(USER_INPUT, data={"input": "hello"}))
    
    # Both should process
    # ...
```

### **Integration Tests**
```bash
# Run full test suite at each phase
pytest tests/ -v

# Run benchmarks to check performance
python scripts/sophia_real_world_benchmark.py

# Run E2E test
python scripts/test_e2e_autonomous_workflow.py
```

### **Manual Testing Checklist**
- [ ] Can chat while Jules task is running
- [ ] Multiple tasks execute concurrently
- [ ] UI updates in real-time
- [ ] Errors don't crash system
- [ ] Can cancel tasks
- [ ] Memory is stored correctly
- [ ] Logs are complete

---

## 📊 Performance Benchmarks

### **Baseline (Blocking Loop)**
```
Task execution time: 100ms
Input latency: 0ms (blocking)
Memory usage: 50MB
CPU usage: 5%
```

### **Target (Event-Driven)**
```
Task execution time: <105ms (max 5% overhead)
Input latency: <50ms (non-blocking)
Memory usage: <60MB (max 20% increase)
CPU usage: <7% (acceptable increase for concurrency)
Concurrent tasks: 10+
```

### **Monitoring**
```python
# Add metrics to track
metrics = {
    "event_bus_throughput": 0,  # events/second
    "task_queue_latency": 0,    # ms from creation to start
    "concurrent_tasks": 0,      # active tasks
    "memory_usage": 0,          # MB
    "cpu_usage": 0              # %
}
```

---

## 🚨 Rollback Plan

### **If Issues Arise:**

1. **Immediate Rollback** (< 5 minutes)
   ```bash
   # Restart with blocking mode
   python run.py --use-blocking
   ```

2. **Code Rollback** (< 30 minutes)
   ```bash
   # Revert to previous commit
   git revert <migration-commit>
   git push
   ```

3. **Feature Flag Disable** (< 5 minutes)
   ```python
   # In kernel.py
   use_event_driven = False  # Force disable
   ```

### **Known Risks & Mitigations**

| Risk | Impact | Mitigation |
|------|--------|------------|
| Event loop blocks | High | Ensure all handlers are async |
| Memory leak | High | Monitor memory, add cleanup |
| Events lost | Medium | Add event persistence |
| Performance regression | Medium | Benchmark at each step |
| Plugin incompatibility | Low | Keep backwards compat |

---

## 📅 Timeline

```
Day 1-2:  Phase 1 - Foundation
Day 3-4:  Phase 2 - Parallel Run
Day 5-6:  Phase 3 - Gradual Cutover
Day 7:    Phase 4 - Plugin Migration
Day 8:    Phase 5 - Enable by Default
Day 9-10: Phase 6 - Cleanup (after stability confirmed)

Total: 10 days for full migration
```

---

## ✅ Success Criteria

- [ ] All existing tests pass
- [ ] New event system tests pass (>90% coverage)
- [ ] Can respond to user input while executing tasks
- [ ] Performance within acceptable range (<5% overhead)
- [ ] No memory leaks
- [ ] Documentation updated
- [ ] Benchmarks show improvement in concurrency
- [ ] No P0/P1 bugs for 1 week

---

## 🔗 Related Documents

- `EVENT_SYSTEM.md` - Event system design
- `TASK_QUEUE.md` - Task queue design
- `GUARDRAILS.md` - Safety checks during migration
- `docs/en/06_testing_and_validation.md` - Testing strategy

---

**Status:** Ready for Implementation ✅  
**Next Steps:** Begin Phase 1 - Create event infrastructure

---

## 📝 Migration Checklist

### **Before Starting**
- [ ] Read all design specs (EVENT_SYSTEM, TASK_QUEUE, GUARDRAILS)
- [ ] Review `core/kernel.py` thoroughly
- [ ] Set up feature flag system
- [ ] Create git branch `feature/event-driven-migration`
- [ ] Back up database

### **Phase 1**
- [ ] Create `core/events.py`
- [ ] Create `core/event_bus.py`
- [ ] Write event bus tests
- [ ] Create `core/task.py`
- [ ] Create `core/task_queue.py`
- [ ] Write task queue tests
- [ ] Update `SharedContext`

### **Phase 2**
- [ ] Initialize event bus in kernel
- [ ] Start/stop event bus
- [ ] Emit USER_INPUT events
- [ ] Emit TASK_CREATED events
- [ ] Log all events
- [ ] Verify no behavior change

### **Phase 3**
- [ ] Migrate planner to events
- [ ] TaskQueue executes tasks
- [ ] Non-blocking input reading
- [ ] New consciousness loop
- [ ] Feature flag switching

### **Phase 4**
- [ ] Migrate Jules monitor
- [ ] Migrate memory plugins
- [ ] Migrate UI plugins
- [ ] Migrate logging manager

### **Phase 5**
- [ ] Enable by default
- [ ] Add rollback CLI flag
- [ ] Run benchmarks
- [ ] Monitor stability

### **Phase 6**
- [ ] Remove blocking code
- [ ] Remove feature flags
- [ ] Final cleanup
- [ ] Tag release

---

**Good luck with the migration! Take it one phase at a time. 🚀**

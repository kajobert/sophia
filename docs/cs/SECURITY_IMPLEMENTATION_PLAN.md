# 🚨 Bezpečnostní Akční Plán - Implementační Prioritizace

**Účel:** Konkrétní akční plán pro opravu všech identifikovaných bezpečnostních zranitelností  
**Datum vytvoření:** 27. října 2025  
**Stav:** 📋 PLÁN K IMPLEMENTACI  

---

## ⚡ EMERGENCY PHASE (OKAMŽITĚ - před jakýmkoliv dalším vývojem)

**Časový rámec:** 1-2 dny  
**Blocking:** Roadmap 04 autonomní režim NESMÍ být spuštěn bez těchto oprav

### E1: Path Traversal Fix v tool_file_system.py
**Závažnost:** 🔴 CRITICAL (CVSS 8.8)  
**Soubor:** `plugins/tool_file_system.py`  
**Řádky:** 60-88

```python
def _get_safe_path(self, user_path: str) -> Path:
    """OPRAVENÁ VERZE - prevents ALL path traversal."""
    if self.sandbox_path is None:
        raise ValueError("Sandbox path not configured.")
    
    # 1. Normalize BEFORE combining
    normalized = os.path.normpath(user_path)
    
    # 2. REJECT any path with .. (CRITICAL!)
    if ".." in normalized:
        raise PermissionError(f"Path traversal blocked: {user_path}")
    
    # 3. REJECT absolute paths
    if os.path.isabs(normalized):
        raise PermissionError(f"Absolute paths not allowed: {user_path}")
    
    # 4. Combine with sandbox
    safe_path = (self.sandbox_path / normalized).resolve()
    
    # 5. VERIFY still within sandbox
    try:
        safe_path.relative_to(self.sandbox_path)
    except ValueError:
        raise PermissionError(f"Path escapes sandbox: {user_path} → {safe_path}")
    
    return safe_path

# PŘIDAT protected paths check
PROTECTED_PATHS = ["core/", "config/settings.yaml", ".git/", ".env", "plugins/base_plugin.py"]

def write_file(self, path: str, content: str) -> str:
    # PŘED safe_path check
    if any(protected in path for protected in self.PROTECTED_PATHS):
        raise PermissionError(f"Protected path: {path}")
    
    safe_path = self._get_safe_path(path)
    # ... rest
```

**Test:**
```bash
pytest tests/security/test_path_traversal.py -v
```

---

### E2: Command Whitelist v tool_bash.py
**Závažnost:** 🔴 CRITICAL (CVSS 9.8)  
**Soubor:** `plugins/tool_bash.py`  
**Řádky:** 13-28, 100-155

```python
# AKTUALIZOVAT ALLOWED_COMMANDS
ALLOWED_COMMANDS = {
    # File operations (read-only)
    "ls", "cat", "head", "tail", "file", "stat", "find", "grep", "wc", "diff",
    
    # Git (read-only)
    "git status", "git log", "git diff", "git show", "git branch",
    
    # Python/Testing
    "python -m pytest", "pytest", "black --check", "ruff check", "mypy",
    
    # System info (read-only)
    "pwd", "whoami", "env", "echo", "date",
    
    # NO: rm, dd, wget, curl, nc, eval, exec, etc.
}

def _is_command_allowed(self, command: str) -> Tuple[bool, str]:
    """STRICT whitelist validation."""
    base_cmd = command.split()[0] if command.split() else ""
    
    # Check whitelist
    is_allowed = any(
        command.startswith(allowed) or command == allowed
        for allowed in self.ALLOWED_COMMANDS
    )
    
    if not is_allowed:
        return False, f"Command '{base_cmd}' not in whitelist"
    
    # ADDITIONAL: Block shell metacharacters
    dangerous_chars = ["|", "&&", "||", ";", "`", "$(", ">", "<", ">>"]
    for char in dangerous_chars:
        if char in command:
            return False, f"Shell metacharacter '{char}' not allowed"
    
    # ADDITIONAL: Block -c flag (code injection)
    if " -c " in command:
        return False, "Code injection via -c flag blocked"
    
    return True, ""

async def execute_command(self, command: str) -> Tuple[int, str, str]:
    # VALIDATE FIRST
    is_allowed, reason = self._is_command_allowed(command)
    if not is_allowed:
        logger.error(f"BLOCKED: {command} - {reason}")
        return -1, "", f"SecurityError: {reason}"
    
    # ... rest of execution
```

**Test:**
```bash
pytest tests/security/test_command_injection.py -v
```

---

### E3: Plan Validation v cognitive_planner.py
**Závažnost:** 🔴 CRITICAL (CVSS 9.8)  
**Soubor:** `plugins/cognitive_planner.py`  
**Řádky:** 130-168

**AKTUALIZACE: _validate_plan_safety je již implementována!**

Pouze **ZAJISTIT že se volá**:

```python
async def execute(self, context: SharedContext) -> SharedContext:
    # ... existing code ...
    
    try:
        plan = json.loads(plan_str)
        
        # VALIDATE plan (ALREADY IMPLEMENTED!)
        is_safe, reason = self._validate_plan_safety(plan)
        if not is_safe:
            logger.error(f"Plan validation failed: {reason}")
            context.payload["plan"] = []
            context.payload["plan_error"] = f"Security: {reason}"
            return context
        
        context.payload["plan"] = plan
        # ...
```

**Test:**
```bash
pytest tests/security/test_prompt_injection.py -v
```

---

### E4: API Keys → Environment Variables
**Závažnost:** 🟠 HIGH (CVSS 7.5)  
**Soubor:** `config/settings.yaml`, `plugins/tool_llm.py`

**OVĚŘENÍ že settings.yaml používá ${ENV_VAR}:**

```yaml
# config/settings.yaml - ALREADY CORRECT! 
llm:
  api_key: "${OPENROUTER_API_KEY}"  # ✅ Správně

tool_web_search:
  google_api_key: "${GOOGLE_API_KEY}"  # ✅ Správně
  google_cse_id: "${GOOGLE_CSE_ID}"  # ✅ Správně
```

**PŘIDAT validaci v tool_llm.py:**

```python
def _validate_api_key(self, api_key: str) -> bool:
    """Validate API key format."""
    # OpenRouter format: sk-or-v1-...
    if not api_key.startswith("sk-or-v1-"):
        logger.error("Invalid API key format")
        return False
    
    if len(api_key) < 40:
        logger.error("API key too short")
        return False
    
    if not re.match(r'^[a-zA-Z0-9\-_]+$', api_key):
        logger.error("API key contains invalid characters")
        return False
    
    return True

def setup(self, config: dict):
    # ... existing code ...
    if api_key_config:
        try:
            api_key = self._resolve_env_vars(api_key_config)
            
            # VALIDATE before using
            if not self._validate_api_key(api_key):
                raise SecurityError("Invalid API key format")
            
            self.api_key = api_key
```

---

## 🔴 PHASE 0: YAML Security (1 den)

### P0.1: Strict YAML Loading
**Soubor:** `core/kernel.py`  
**Řádky:** 27-33

```python
from yaml import SafeLoader

class StrictYAMLLoader(SafeLoader):
    """YAML loader that rejects !!python tags."""
    pass

# Remove dangerous constructors
for tag in ['python/object', 'python/object/new', 'python/object/apply']:
    if tag in StrictYAMLLoader.yaml_constructors:
        del StrictYAMLLoader.yaml_constructors[tag]

def _setup_plugins(self):
    config_path = Path("config/settings.yaml")
    
    with open(config_path, "r") as f:
        raw_yaml = f.read()
        
        # CHECK for !!python tags
        if "!!python" in raw_yaml:
            raise SecurityError("Dangerous YAML tag '!!python' detected")
        
        # LOAD with strict loader
        config = yaml.load(raw_yaml, Loader=StrictYAMLLoader)
```

**Test:**
```python
pytest tests/security/test_advanced_attacks.py::test_yaml_deserialization_blocked -v
```

---

### P0.2: Config Schema Validation
**Nový soubor:** `core/config_validator.py`

```python
from pydantic import BaseModel, validator
from typing import Dict, Optional

class LLMConfig(BaseModel):
    model: str
    api_key: str
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v.startswith("${") or not v.endswith("}"):
            raise ValueError("API key must be env var: ${VAR_NAME}")
        return v

class PluginConfig(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = None
    timeout: Optional[int] = None

class SophiaConfig(BaseModel):
    llm: LLMConfig
    plugins: Dict[str, PluginConfig] = {}

# In kernel.py
from core.config_validator import SophiaConfig

def _setup_plugins(self):
    # ... load YAML ...
    
    # VALIDATE schema
    validated_config = SophiaConfig(**config)
    config = validated_config.dict()
```

---

### P0.3: File Integrity Monitoring
**Nový soubor:** `core/integrity_monitor.py`

```python
import hashlib
from pathlib import Path

class IntegrityMonitor:
    CRITICAL_FILES = {
        "config/settings.yaml": None,  # Hash computed at startup
        "core/kernel.py": None,
        "core/plugin_manager.py": None,
        "plugins/base_plugin.py": None,
    }
    
    def __init__(self):
        # Compute hashes at startup
        for filepath in self.CRITICAL_FILES:
            self.CRITICAL_FILES[filepath] = self._hash_file(filepath)
    
    def _hash_file(self, filepath: str) -> str:
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def verify_integrity(self):
        """Check if critical files were modified."""
        for filepath, expected_hash in self.CRITICAL_FILES.items():
            actual_hash = self._hash_file(filepath)
            if actual_hash != expected_hash:
                raise SecurityError(f"TAMPERED: {filepath}")

# In kernel.py __init__
def __init__(self):
    self.integrity_monitor = IntegrityMonitor()
    self.integrity_monitor.verify_integrity()
    # ... rest
```

---

## 🔴 PHASE 1: Memory Security (2-3 dny)

### P1.1: Message Signing v memory_sqlite.py
**Soubor:** `plugins/memory_sqlite.py`

```python
import hmac
import hashlib
import secrets

class SQLiteMemory(BasePlugin):
    def __init__(self):
        super().__init__()
        # Ephemeral signing key (regenerated each startup)
        self.signing_key = secrets.token_bytes(32)
    
    def _sign_message(self, role: str, content: str, timestamp: str) -> str:
        data = f"{role}|{content}|{timestamp}".encode()
        return hmac.new(self.signing_key, data, hashlib.sha256).hexdigest()
    
    def setup(self, config: dict):
        # ... existing setup ...
        
        # ADD signature column to table
        self.history_table = Table(
            "conversation_history",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("session_id", String),
            Column("role", String),
            Column("content", String),
            Column("timestamp", String),  # NEW
            Column("signature", String),  # NEW
        )
        self.metadata.create_all(self.engine)
    
    async def execute(self, context: SharedContext):
        llm_response = context.payload.get("llm_response")
        
        if llm_response:
            timestamp = datetime.now().isoformat()
            signature = self._sign_message("assistant", llm_response, timestamp)
            
            with self.engine.connect() as conn:
                conn.execute(
                    insert(self.history_table).values(
                        session_id=context.session_id,
                        role="assistant",
                        content=llm_response,
                        timestamp=timestamp,
                        signature=signature
                    )
                )
                conn.commit()
        
        return context
    
    def get_history(self, session_id: str, limit: int = 10):
        with self.engine.connect() as conn:
            stmt = select(
                self.history_table.c.role,
                self.history_table.c.content,
                self.history_table.c.timestamp,
                self.history_table.c.signature
            ).where(...)
            
            results = conn.execute(stmt).fetchall()
        
        verified_history = []
        for role, content, timestamp, signature in results:
            # VERIFY signature
            expected_sig = self._sign_message(role, content, timestamp)
            if expected_sig != signature:
                logger.error(f"TAMPERED message: {content[:50]}")
                continue  # Skip tampered
            
            verified_history.append({"role": role, "content": content})
        
        return verified_history
```

**Test:**
```python
pytest tests/security/test_advanced_attacks.py::test_message_signature_prevents_injection -v
```

---

### P1.2: ChromaDB Provenance v memory_chroma.py
**Soubor:** `plugins/memory_chroma.py`

```python
def add_memory(self, session_id: str, text: str) -> None:
    """Add memory with provenance tracking."""
    timestamp = datetime.now().isoformat()
    
    metadata = {
        "session_id": session_id,
        "created_at": timestamp,
        "created_by": "sophia_core",  # Source verification
        "trust_score": 1.0,  # High trust for direct user interaction
        "verified": True,
        "source": "user_interaction"
    }
    
    doc_id = f"{session_id}_{hash(text)}"
    self.collection.add(
        documents=[text],
        metadatas=[metadata],
        ids=[doc_id]
    )

def search_memories(self, query_text: str, n_results: int = 3):
    """Search with trust filtering."""
    results = self.collection.query(
        query_texts=[query_text],
        n_results=n_results * 2,  # Get extra for filtering
        where={"verified": True}  # Only verified memories
    )
    
    # Filter by trust score
    filtered = []
    for i, doc in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i]
        trust = metadata.get("trust_score", 0.0)
        
        if trust >= 0.5:  # Threshold
            filtered.append(doc)
        else:
            logger.warning(f"Low trust filtered: {doc[:50]}")
    
    return filtered[:n_results]
```

---

## 🔴 PHASE 2: Plugin Security (3-4 dny)

### P2.1: Atomic Plugin Loading
**Soubor:** `core/plugin_manager.py`

```python
import fcntl
import time

class PluginManager:
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = Path(plugin_dir)
        self._plugins = {pt: [] for pt in PluginType}
        
        # Snapshot BEFORE loading
        self.initial_snapshot = self._snapshot_plugins()
        
        # Load with lock
        self.load_plugins_atomic()
    
    def _snapshot_plugins(self):
        """Snapshot plugin files and modification times."""
        return {
            f.name: f.stat().st_mtime
            for f in self.plugin_dir.glob("*.py")
            if not f.name.startswith("_")
        }
    
    def load_plugins_atomic(self):
        """Load with race condition protection."""
        lockfile = self.plugin_dir / ".plugin_load.lock"
        
        with open(lockfile, "w") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            
            try:
                # Verify no changes
                current = self._snapshot_plugins()
                
                for name, mtime in current.items():
                    if name not in self.initial_snapshot:
                        raise SecurityError(f"New plugin: {name}")
                    
                    if mtime > self.initial_snapshot[name]:
                        raise SecurityError(f"Modified: {name}")
                
                # Safe to load
                self.load_plugins()
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
```

---

### P2.2: Plugin Name Collision Detection
**Soubor:** `core/plugin_manager.py`

```python
def _register_plugin(self, plugin_class: Type[BasePlugin]):
    plugin_instance = plugin_class()
    name = plugin_instance.name
    
    # CHECK for duplicates
    all_existing = [p for plugins in self._plugins.values() for p in plugins]
    if any(p.name == name for p in all_existing):
        raise SecurityError(f"Duplicate plugin name: {name}")
    
    # Register
    self._plugins[plugin_instance.plugin_type].append(plugin_instance)
    logger.info(f"Registered: {name}")
```

---

## 🟡 PHASE 3: Monitoring & Logging (2 dny)

### P3.1: Structured Logging
**Nový soubor:** `core/secure_logger.py`

```python
import json
import logging
import re
import unicodedata

class StructuredLogFormatter(logging.Formatter):
    """JSON format logs - prevents injection."""
    
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": self.sanitize(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        return json.dumps(log_data)
    
    @staticmethod
    def sanitize(message: str, max_length: int = 500) -> str:
        """Remove dangerous characters."""
        # Remove newlines
        sanitized = message.replace('\n', '\\n').replace('\r', '\\r')
        
        # Remove ANSI codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        sanitized = ansi_escape.sub('', sanitized)
        
        # Remove control characters
        sanitized = ''.join(
            char for char in sanitized
            if unicodedata.category(char)[0] != "C" or char in ['\t']
        )
        
        # Truncate
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "...[TRUNCATED]"
        
        return sanitized

# Setup in run.py nebo kernel.py
handler = logging.StreamHandler()
handler.setFormatter(StructuredLogFormatter())
logging.root.addHandler(handler)
```

---

## 📊 Implementační Timeline

| Fáze | Dny | Priorita | Blokuje Roadmap 04? |
|------|-----|----------|---------------------|
| EMERGENCY | 1-2 | P0 | ✅ ANO |
| Phase 0: YAML | 1 | P0 | ✅ ANO |
| Phase 1: Memory | 2-3 | P0 | ✅ ANO |
| Phase 2: Plugins | 3-4 | P1 | ⚠️ DOPORUČENO |
| Phase 3: Logging | 2 | P2 | ❌ NE |

**Celkem:** 9-12 dní pro kompletní implementaci

---

## ✅ Verifikační Checklist

Po každé fázi spusť:

```bash
# Security test suite
pytest tests/security/ -v --tb=short

# Specific attack tests
pytest tests/security/test_advanced_attacks.py -v
pytest tests/security/test_integration_attacks.py -v
pytest tests/security/test_command_injection.py -v
pytest tests/security/test_path_traversal.py -v

# Full test suite (must all pass)
pytest tests/ -v
```

---

## 🚨 Final Acceptance Criteria

Před nasazením do produkce MUSÍ být splněno:

- [ ] ✅ Všechny EMERGENCY opravy implementovány
- [ ] ✅ Všechny P0 opravy implementovány
- [ ] ✅ 100% security test suite prochází
- [ ] ✅ 100% regular test suite prochází (317 tests)
- [ ] ✅ Code review od security specialisty
- [ ] ✅ Penetration testing dokončeno
- [ ] ✅ Dokumentace aktualizována
- [ ] ✅ Incident response plan vytvořen

---

*Tento dokument slouží jako implementační guide. Každá změna by měla být provedena s code review a testováním.*

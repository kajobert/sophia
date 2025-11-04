# Jules API Pydantic Integration

## Přehled

Plugin `tool_jules.py` nyní používá **Pydantic v2** pro validaci dat a type safety. To přináší:

- ✅ **Automatická validace** - nevalidní data jsou okamžitě odmítnuta
- ✅ **Type safety** - IDE autocomplete a type checking
- ✅ **Jasné chybové hlášky** - víte přesně, co je špatně
- ✅ **Runtime kontrola** - chyby jsou odhaleny dříve
- ✅ **Snadná serializace** - model ↔ JSON/dict automaticky

## Pydantic Modely

### JulesSession

Reprezentuje jednu Jules coding session.

```python
from plugins.tool_jules import JulesSession

session = JulesSession(
    name="sessions/abc123",
    title="My Coding Task",
    prompt="Create a Flask app",
    state="ACTIVE",
    create_time="2025-11-02T12:00:00Z"
)

# Type-safe přístup
print(session.name)       # str
print(session.title)      # Optional[str]
print(session.state)      # Optional[str]
```

**Validace:**
- `name` MUSÍ začínat `"sessions/"`
- Všechna pole kromě `name` jsou optional

### JulesSessionList

Seznam sessions s podporou pagination.

```python
from plugins.tool_jules import JulesSessionList

sessions = JulesSessionList(
    sessions=[
        JulesSession(name="sessions/123", title="Task 1"),
        JulesSession(name="sessions/456", title="Task 2")
    ],
    next_page_token="abc123"
)

# Iterace přes sessions
for session in sessions.sessions:
    print(session.title)
```

### JulesSource

Reprezentuje GitHub repository dostupný pro Jules.

```python
from plugins.tool_jules import JulesSource

source = JulesSource(
    name="sources/github/owner/repo",
    display_name="My Project",
    description="A cool web app"
)
```

### CreateSessionRequest

Validace parametrů pro vytvoření nové session.

```python
from plugins.tool_jules import CreateSessionRequest
from pydantic import ValidationError

# Validní request
request = CreateSessionRequest(
    prompt="Add authentication",
    source="sources/github/myorg/myapp",
    branch="develop",
    title="Auth Feature",
    auto_pr=True
)

# Automatická validace
try:
    bad_request = CreateSessionRequest(
        prompt="",  # Prázdný prompt = chyba!
        source="invalid/format"  # Špatný formát = chyba!
    )
except ValidationError as e:
    print(e.errors())
```

**Validační pravidla:**
- `prompt`: Nesmí být prázdný (min_length=1)
- `source`: Musí odpovídat pattern `^sources/github/[\w-]+/[\w-]+$`
- `branch`: Default "main"
- `auto_pr`: Default False

## Použití v Plugin Metodách

### list_sessions() → JulesSessionList

```python
from core.context import SharedContext
from plugins.tool_jules import JulesAPITool

tool = JulesAPITool()
sessions = tool.list_sessions(context)

# Type-safe response
print(f"Found {len(sessions.sessions)} sessions")
for session in sessions.sessions:
    print(f"{session.name}: {session.title} [{session.state}]")
```

### create_session() → JulesSession

```python
session = tool.create_session(
    context=context,
    prompt="Build a TODO app with React",
    source="sources/github/myorg/myrepo",
    title="TODO App",
    auto_pr=True
)

# Validated response
print(f"Created session: {session.name}")
print(f"Status: {session.state}")
```

### get_session() → JulesSession

```python
session = tool.get_session(context, "abc123")

# Type-safe access
if session.state == "COMPLETED":
    print(f"Session {session.title} is complete!")
```

### list_sources() → JulesSourceList

```python
sources = tool.list_sources(context)

for source in sources.sources:
    print(f"{source.display_name}: {source.name}")
```

## Error Handling

### JulesValidationError

Pokud API vrátí nevalidní data, plugin vyhodí `JulesValidationError`:

```python
from plugins.tool_jules import JulesValidationError

try:
    session = tool.get_session(context, "invalid_id")
except JulesValidationError as e:
    print(f"Invalid data from API: {e}")
except JulesAPIError as e:
    print(f"API error: {e}")
```

## Testing

Spusťte test suite pro ověření Pydantic validace:

```bash
cd /workspaces/sophia
source .venv/bin/activate
PYTHONPATH=/workspaces/sophia python scripts/test_jules_pydantic.py
```

Testy pokrývají:
1. ✅ Validaci JulesSession modelu
2. ✅ Validaci CreateSessionRequest
3. ✅ Validaci JulesSessionList
4. ✅ Type safety benefity
5. ✅ Serializaci modelů

## Benefits vs. Plain Dicts

### Před Pydantic (Dict)

```python
# ❌ Žádná validace
session = {"name": "invalid", "title": "Test"}

# ❌ Typos nejsou odhaleny
print(session["titel"])  # KeyError runtime!

# ❌ IDE neví, jaká pole existují
session["???"]  # Žádný autocomplete
```

### S Pydantic (Model)

```python
# ✅ Automatická validace
try:
    session = JulesSession(name="invalid", title="Test")
except ValidationError:
    print("Invalid session name!")

# ✅ Typos odhaleny při vývoji
print(session.titel)  # IDE warning + AttributeError

# ✅ Full autocomplete
session.  # IDE nabídne: name, title, prompt, state, ...
```

## Integration s Sophie

Sophie automaticky používá Pydantic modely:

```bash
python run.py "Sophie, use tool_jules to list all sessions"
```

**Log výstup:**
```
Making GET request to Jules API: sessions
Step 'list_sessions' executed. Result: sessions=[] next_page_token=None
```

Všimněte si: `sessions=[]` místo `{}` - to je Pydantic model!

## Závěr

Pydantic integrace zajišťuje:
- **Robustnost**: Nevalidní data nemohou projít
- **Bezpečnost**: Type-safe kód snižuje bugy
- **Developer Experience**: Lepší IDE podpora
- **Maintainability**: Jasná struktura dat

---

**Autor:** GitHub Copilot  
**Datum:** 2025-11-02  
**Pydantic verze:** 2.12.3

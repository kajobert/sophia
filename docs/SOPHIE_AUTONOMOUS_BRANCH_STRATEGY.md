# Sophie's Autonomous Branch Strategy

## 🎯 Cíl

Sophie pracuje **autonomně** ve své vlastní větvi a **požaduje lidské schválení** před mergem do `master`.

## 📋 Workflow

### 1. Sophie's Working Branch

```yaml
# config/settings.yaml - NOVÁ SEKCE
autonomous_workflow:
  enabled: true
  working_branch: "sophie/autonomous-dev"  # Sophie's hlavní pracovní větev
  auto_merge_to_master: false              # Nikdy nemerge do master automaticky!
  require_human_approval: true             # Vždy vyžaduje lidské schválení
  pr_labels: ["autonomous", "sophie-generated", "needs-review"]
```

### 2. Kompletní Autonomní Cyklus

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. DELEGACE K JULESOVI                                          │
├─────────────────────────────────────────────────────────────────┤
│ Sophie: "Potřebuji feature X"                                   │
│   ↓                                                              │
│ jules.create_session(                                            │
│   source="sources/github/ShotyCZ/sophia",                       │
│   branch="sophie/autonomous-dev",  ← Sophie's pracovní větev    │
│   prompt="Implementuj feature X",                               │
│   auto_pr=False  ← DŮLEŽITÉ! Jules nečeká na potvrzení          │
│ )                                                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. MONITORING JULES COMPLETION                                  │
├─────────────────────────────────────────────────────────────────┤
│ monitor.monitor_until_completion(session_id)                    │
│   ↓                                                              │
│ Jules states:                                                    │
│   PLANNING → IN_PROGRESS → COMPLETED ✅                         │
│                                                                  │
│ ⚠️ PROBLÉM: Jules skončil, ale PR NENÍ na GitHubu!              │
│            V Jules UI je tlačítko "Submit the change"           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. POTVRZENÍ JULES PR (CHYBÍ V API!)                            │
├─────────────────────────────────────────────────────────────────┤
│ ❌ CURRENT STATE: Jules API nemá metodu pro submit PR           │
│                                                                  │
│ POTŘEBUJEME:                                                     │
│ jules.approve_session_pr(context, session_id)                   │
│   nebo                                                           │
│ jules.submit_changes(context, session_id)                       │
│                                                                  │
│ WORKAROUND (dočasný):                                            │
│ 1. Sophie loguje: "⚠️ Jules session completed, manual PR submit │
│    required at: https://jules.google.com/session/123"           │
│ 2. Vytvoří GitHub issue pro člověka                             │
│ 3. Čeká na PR od Jules                                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. DETEKCE JULES PR NA GITHUBU                                  │
├─────────────────────────────────────────────────────────────────┤
│ # Sophie pravidelně checkuje nové PRs                           │
│ prs = github.list_pull_requests(                                │
│   owner="ShotyCZ",                                              │
│   repo="sophia",                                                │
│   state="open",                                                 │
│   head="jules-session-123"  # Jules vytvoří branch              │
│ )                                                                │
│                                                                  │
│ if pr_found and pr.created_by_jules:                            │
│   → Pokračuj krokem 5                                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. SOPHIE REVIEW A TEST                                         │
├─────────────────────────────────────────────────────────────────┤
│ # Sophie analyzuje PR od Jules                                  │
│ pr_details = github.get_pull_request(pr_number)                 │
│                                                                  │
│ # Sophie zkontroluje změny                                      │
│ files = github.get_pr_files(pr_number)                          │
│ diff = github.get_pr_diff(pr_number)                            │
│                                                                  │
│ # Sophie spustí testy                                           │
│ bash.execute("pytest tests/")                                   │
│                                                                  │
│ # Sophie analyzuje pomocí LLM                                   │
│ analysis = llm.analyze(                                         │
│   f"Review this PR diff: {diff}"                                │
│ )                                                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. SOPHIE MERGE DO PRACOVNÍ VĚTVE                               │
├─────────────────────────────────────────────────────────────────┤
│ if analysis.looks_good and tests_passed:                        │
│   # Sophie merge do SVÉ větve                                   │
│   github.merge_pull_request(                                    │
│     owner="ShotyCZ",                                            │
│     repo="sophia",                                              │
│     pull_number=pr.number,                                      │
│     merge_method="squash",                                      │
│     # Merge do: sophie/autonomous-dev (NE master!)              │
│   )                                                              │
│                                                                  │
│   context.logger.info(                                          │
│     "✅ Merged Jules PR into sophie/autonomous-dev"             │
│   )                                                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. SOPHIE VYTVOŘÍ PR PRO LIDSKÉ SCHVÁLENÍ                       │
├─────────────────────────────────────────────────────────────────┤
│ # Sophie vytvoří PR: sophie/autonomous-dev → master             │
│ human_pr = github.create_pull_request(                          │
│   owner="ShotyCZ",                                              │
│   repo="sophia",                                                │
│   title="[SOPHIE] Autonomous improvements batch #42",           │
│   body=f"""                                                      │
│   ## Sophie's Autonomous Work Summary                           │
│                                                                  │
│   This PR contains changes autonomously implemented by Sophie.  │
│                                                                  │
│   ### Features Implemented:                                     │
│   - Feature X (Jules session: sessions/123)                     │
│   - Bug fix Y (Jules session: sessions/456)                     │
│                                                                  │
│   ### Tests:                                                     │
│   ✅ All tests passing                                          │
│   ✅ No security vulnerabilities detected                       │
│   ✅ Performance metrics acceptable                             │
│                                                                  │
│   ### Jules Sessions:                                            │
│   - sessions/123: Add feature X                                 │
│   - sessions/456: Fix bug Y                                     │
│                                                                  │
│   **NEEDS HUMAN REVIEW** before merging to master.              │
│   """,                                                           │
│   head="sophie/autonomous-dev",                                 │
│   base="master",                                                │
│   labels=["autonomous", "sophie-generated", "needs-review"]     │
│ )                                                                │
│                                                                  │
│ # Sophie přidá komentář s detaily                               │
│ github.add_comment(                                             │
│   pr_number=human_pr.number,                                    │
│   body="✨ Hi! I've autonomously implemented these changes..."  │
│ )                                                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. ČEKÁNÍ NA LIDSKÉ SCHVÁLENÍ                                   │
├─────────────────────────────────────────────────────────────────┤
│ # Sophie monitoruje stav PR                                     │
│ while True:                                                      │
│   pr_status = github.get_pull_request(human_pr.number)          │
│                                                                  │
│   if pr_status.merged:                                          │
│     context.logger.info("✅ Human approved and merged!")        │
│     break                                                        │
│                                                                  │
│   if pr_status.closed and not pr_status.merged:                 │
│     context.logger.warning("❌ PR rejected by human")           │
│     # Sophie analyzuje feedback a učí se                        │
│     break                                                        │
│                                                                  │
│   # Check každých 5 minut                                       │
│   time.sleep(300)                                                │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Implementace

### 1. Rozšíření tool_github o chybějící metody

```python
# plugins/tool_github.py - PŘIDAT:

def list_pull_requests(
    self,
    context: SharedContext,
    owner: str,
    repo: str,
    state: str = "open",
    head: Optional[str] = None,
    base: Optional[str] = None
) -> List[PullRequestResponse]:
    """Lists pull requests with optional filtering."""
    params = {"state": state}
    if head:
        params["head"] = f"{owner}:{head}"
    if base:
        params["base"] = base
    
    response = self._make_request("GET", f"repos/{owner}/{repo}/pulls", params)
    return [PullRequestResponse(**pr) for pr in response]

def get_pull_request(
    self,
    context: SharedContext,
    owner: str,
    repo: str,
    pull_number: int
) -> PullRequestResponse:
    """Gets detailed info about a PR."""
    response = self._make_request("GET", f"repos/{owner}/{repo}/pulls/{pull_number}")
    return PullRequestResponse(**response)

def get_pull_request_files(
    self,
    context: SharedContext,
    owner: str,
    repo: str,
    pull_number: int
) -> List[Dict[str, Any]]:
    """Gets list of files changed in PR."""
    return self._make_request("GET", f"repos/{owner}/{repo}/pulls/{pull_number}/files")

def get_pull_request_diff(
    self,
    context: SharedContext,
    owner: str,
    repo: str,
    pull_number: int
) -> str:
    """Gets PR diff in unified format."""
    # GitHub API can return diff with Accept header
    response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}",
        headers={**self.session.headers, "Accept": "application/vnd.github.v3.diff"}
    )
    return response.text
```

### 2. Nový Plugin: cognitive_sophie_autonomy

```python
# plugins/cognitive_sophie_autonomy.py

class SophieAutonomyOrchestrator(BasePlugin):
    """
    Orchestrates Sophie's autonomous development workflow.
    
    Manages:
    - Working branch strategy
    - Jules PR detection and merging
    - Human approval requests
    - Safety checks
    """
    
    def __init__(self):
        self.working_branch = "sophie/autonomous-dev"
        self.jules_tool = None
        self.github_tool = None
        self.monitor_tool = None
    
    async def autonomous_feature_cycle(
        self,
        context: SharedContext,
        feature_description: str
    ):
        """
        Complete autonomous cycle:
        1. Delegate to Jules
        2. Monitor completion
        3. Detect Jules PR
        4. Review and test
        5. Merge to sophie/autonomous-dev
        6. Create PR for human approval
        """
        
        # Step 1: Delegate to Jules
        session = await self.jules_tool.create_session(
            context,
            prompt=feature_description,
            source="sources/github/ShotyCZ/sophia",
            branch=self.working_branch,
            auto_pr=False  # Jules nebude čekat na potvrzení
        )
        
        # Step 2: Monitor
        status = await self.monitor_tool.monitor_until_completion(
            context,
            session_id=session.name
        )
        
        if not status.is_completed:
            raise RuntimeError("Jules failed to complete task")
        
        # Step 3: Wait for Jules PR (WORKAROUND - dokud nemáme submit API)
        context.logger.warning(
            f"⚠️ Jules session completed. Manual PR approval needed at: "
            f"https://jules.google.com/session/{session.name.split('/')[1]}"
        )
        
        # Create issue for human to approve Jules PR
        issue = await self.github_tool.create_issue(
            context,
            owner="ShotyCZ",
            repo="sophia",
            title=f"Action Required: Approve Jules PR for session {session.name}",
            body=f"""
            Jules has completed the task but needs manual PR approval.
            
            1. Go to: https://jules.google.com/session/{session.name.split('/')[1]}
            2. Click "Submit the change"
            3. Wait for PR to appear on GitHub
            
            Jules session: {session.name}
            Task: {feature_description}
            """,
            labels=["jules-approval-needed", "autonomous"]
        )
        
        # Step 4: Wait for Jules PR on GitHub
        jules_pr = await self._wait_for_jules_pr(context, session.name)
        
        # Step 5: Review and test
        if await self._review_and_test_pr(context, jules_pr):
            # Step 6: Merge to Sophie's working branch
            await self.github_tool.merge_pull_request(
                context,
                owner="ShotyCZ",
                repo="sophia",
                pull_number=jules_pr.number,
                merge_method="squash"
            )
            
            # Step 7: Create PR for human approval
            await self._create_human_approval_pr(context, jules_pr, session)
    
    async def _wait_for_jules_pr(
        self,
        context: SharedContext,
        session_id: str,
        timeout: int = 3600
    ):
        """Waits for Jules to create PR after manual approval."""
        start = datetime.now()
        
        while (datetime.now() - start).total_seconds() < timeout:
            prs = await self.github_tool.list_pull_requests(
                context,
                owner="ShotyCZ",
                repo="sophia",
                state="open"
            )
            
            # Jules creates branches like: jules-<session-id>
            session_num = session_id.split("/")[1]
            jules_branch = f"jules-{session_num}"
            
            for pr in prs:
                if jules_branch in pr.head:
                    context.logger.info(f"✅ Found Jules PR: #{pr.number}")
                    return pr
            
            await asyncio.sleep(60)  # Check every minute
        
        raise TimeoutError("Jules PR not found within timeout")
```

## 🚧 Co Chybí

### 1. Jules API - Submit PR Method

**POTŘEBA:**
```python
# V tool_jules.py
def submit_session_pr(
    self,
    context: SharedContext,
    session_id: str
) -> Dict[str, Any]:
    """
    Submits/approves the PR from a completed Jules session.
    
    This is equivalent to clicking "Submit the change" in Jules UI.
    """
    return self._make_request(
        context,
        "POST",
        f"sessions/{session_id}:submitPullRequest"
    )
```

**DOTAZ PRO JULES TEAM:**
- Existuje API endpoint pro programmatic PR approval?
- Jak můžeme automatizovat "Submit the change" button?
- Dokumentace: https://developers.google.com/jules/api/reference/rest/v1alpha/sessions

### 2. GitHub - List PRs

Již implementováno výše ✅

### 3. Sophie Config - Working Branch

```yaml
# config/settings.yaml
autonomous_workflow:
  working_branch: "sophie/autonomous-dev"
  auto_merge_to_master: false
  require_human_approval: true
```

## 📊 Bezpečnostní Kontroly

Sophie **NIKDY** nemerge do `master` bez lidského schválení:

```python
def _safety_check(self, target_branch: str):
    """Prevents accidental merge to protected branches."""
    PROTECTED_BRANCHES = ["master", "main", "production"]
    
    if target_branch in PROTECTED_BRANCHES:
        raise SecurityError(
            f"Cannot auto-merge to protected branch: {target_branch}. "
            f"Human approval required!"
        )
```

## 🎯 Výhody Této Strategie

✅ **Bezpečnost**: Sophie nemůže pokazit `master`  
✅ **Autonomie**: Sophie může pracovat kontinuálně  
✅ **Kontrola**: Člověk má finální schválení  
✅ **Transparentnost**: Všechny změny viditelné v PRs  
✅ **Rollback**: Snadné vrácení změn  

---

**Next Steps:**
1. Implementovat chybějící GitHub metody
2. Vytvořit cognitive_sophie_autonomy plugin
3. Zjistit od Jules team API pro submit PR
4. Otestovat celý workflow end-to-end

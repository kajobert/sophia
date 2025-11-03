# Sophie's Autonomous Development Workflow

## 🎯 Vision

Sophie je nyní plně autonomní AI agent schopný:
- ✅ Identifikovat potřebné vylepšení
- ✅ Výzkum best practices a dokumentace
- ✅ Delegovat komplexní úkoly Julesovi
- ✅ Monitorovat pokrok asynchronně
- ✅ Testovat a aplikovat změny
- ✅ Vytvářet GitHub issues a pull requesty

## 🛠️ Required Tools

Sophie má tyto nástroje:

### 1. Research & Analysis
- **tool_tavily** - Pokročilé vyhledávání na internetu
- **tool_llm** - Analýza a zpracování informací
- **cognitive_doc_reader** - Čtení dokumentace

### 2. Task Delegation
- **tool_jules** - Delegace coding tasků na Jules API
- **cognitive_jules_monitor** - Monitorování Jules sessions

### 3. Code Management
- **tool_github** - GitHub API (issues, PRs, merging)
- **tool_git** - Git operace (commit, push, branch)
- **tool_code_workspace** - Čtení a editace kódu

### 4. Testing & Quality
- **tool_bash** - Spouštění testů
- **tool_performance_monitor** - Sledování nákladů a výkonu
- **tool_langfuse** - LLM observability

## 📋 Complete Workflow

### Step 1: Identify Improvement

Sophie identifikuje potřebu na základě:
- Uživatelského požadavku
- Chyby v logu
- Missing functionality
- Performance issues

```python
# Sophie's internal thinking:
need = {
    "type": "new_plugin",
    "name": "tool_github_issues",
    "reason": "Need GitHub Issues API for autonomous bug tracking",
    "priority": "high"
}
```

### Step 2: Research

Sophie provede výzkum:

```python
# Search for best practices
research = tavily.advanced_search(
    context,
    query="GitHub Issues API Python implementation best practices",
    max_results=10,
    include_domains=["github.com", "docs.github.com"]
)

# Read documentation
docs = doc_reader.read_documentation(
    context,
    urls=research.relevant_urls
)
```

### Step 3: Create Specification

Sophie analyzuje výsledky:

```python
# Analyze research
spec = llm.generate_text(
    context,
    prompt=f"""
    Based on this research: {research.results}
    
    Create detailed technical specification for:
    - Request/Response Pydantic models
    - API endpoints and methods
    - Error handling strategy
    - Test coverage plan
    """
)
```

### Step 4: Delegate to Jules

Sophie předá úkol Julesovi:

```python
# Create Jules session
session = jules.create_session(
    context,
    source="sources/github/ShotyCZ/sophia",
    branch="master",  # IMPORTANT: Use master, not main!
    prompt=f"""
    Create plugins/tool_github_issues.py
    
    Requirements:
    {spec.requirements}
    
    Implementation details:
    {spec.implementation}
    
    Test coverage:
    {spec.tests}
    """
)

context.logger.info(f"Delegated to Jules: {session.name}")
```

### Step 5: Monitor Progress

Sophie monitoruje asynchronně:

```python
# Start monitoring
monitor.start_monitoring(
    context,
    session_id=session.name,
    check_interval=60,      # Check every minute
    max_duration=3600,      # Max 1 hour
    notify_on_completion=True
)

# Sophie continues with other work...
# Monitor runs in background
```

### Step 6: Check Completion

Sophie periodicky kontroluje:

```python
# Check status
status = monitor.check_session_status(context, session.name)

if status.is_completed:
    context.logger.info("✅ Jules completed!")
    
    # Read Jules results
    summary = status.completion_summary
    
elif status.is_error:
    context.logger.error(f"❌ Jules failed: {status.error_message}")
    
    # Sophie decides: retry, modify, or escalate
```

### Step 7: Test Changes

Sophie testuje výsledky:

```python
# Run tests
test_result = bash.execute(
    context,
    command="python scripts/test_github.py"
)

if test_result.exit_code != 0:
    context.logger.warning("Tests failed - reviewing errors...")
    
    # Sophie can ask Jules to fix
    # Or create GitHub issue for human review
```

### Step 8: Create Pull Request

Sophie vytvoří PR:

```python
# Commit changes (Jules already did this)
# Create PR via GitHub API
pr = github.create_pull_request(
    context,
    owner="ShotyCZ",
    repo="sophia",
    title="Add GitHub Issues API integration",
    body=f"""
    ## Changes
    {summary}
    
    ## Tests
    ✅ All Pydantic validations passing
    ✅ Plugin initialization successful
    ✅ 7 methods implemented
    
    ## Delegated to Jules
    Session: {session.name}
    """,
    head=jules_branch,
    base="master"
)

context.logger.info(f"PR created: {pr.html_url}")
```

### Step 9: Monitor PR Status

Sophie sleduje PR:

```python
# Check PR status
pr_status = github.get_pull_request_status(
    context,
    owner="ShotyCZ",
    repo="sophia",
    pull_number=pr.number
)

# Wait for CI/CD
if pr_status.checks_passed:
    context.logger.info("✅ All checks passed")
else:
    context.logger.warning("⚠️ Some checks failed - investigating...")
```

### Step 10: Merge or Escalate

Sophie rozhodne:

```python
if pr_status.checks_passed and pr_status.reviews_approved:
    # Auto-merge
    github.merge_pull_request(
        context,
        owner="ShotyCZ",
        repo="sophia",
        pull_number=pr.number,
        merge_method="squash"
    )
    
    context.logger.info("✅ Changes merged - I improved myself!")
    
else:
    # Create issue for human review
    issue = github.create_issue(
        context,
        owner="ShotyCZ",
        repo="sophia",
        title="Human review needed: GitHub Issues plugin",
        body=f"PR {pr.html_url} needs review:\n{pr_status.reason}",
        labels=["needs-review", "autonomous-development"]
    )
```

## 🔧 Setup Instructions

### 1. Configure Environment Variables

```bash
# Add to .env or export
export GITHUB_TOKEN="ghp_your_personal_access_token"
export JULES_API_KEY="your_jules_api_key"
export TAVILY_API_KEY="your_tavily_key"  # Already configured
```

### 2. GitHub Token Permissions

Required scopes:
- ✅ `repo` - Full repository access
- ✅ `workflow` - Run GitHub Actions
- ✅ `write:packages` - Package management

Generate at: https://github.com/settings/tokens

### 3. Jules API Setup

Already configured in `tool_jules.py`. See [JULES_API_SETUP.md](JULES_API_SETUP.md).

### 4. Verify Setup

```python
# Test Sophie's capabilities
python -c "
from plugins.tool_github import ToolGitHub
from plugins.cognitive_jules_monitor import CognitiveJulesMonitor
from plugins.tool_jules import JulesAPITool

# Test GitHub
github = ToolGitHub()
github.setup({})
print('✅ GitHub ready')

# Test Jules
jules = JulesAPITool()
jules.setup({})
print('✅ Jules ready')

# Test Monitor
monitor = CognitiveJulesMonitor()
monitor.setup({})
monitor.set_jules_tool(jules)
print('✅ Monitor ready')

print('🎉 Sophie is ready for autonomous development!')
"
```

## 📊 Example: Full Autonomous Workflow

### Scenario: Sophie Discovers Bug

```python
# 1. Sophie detects error in logs
error = log_manager.get_recent_errors(context)

# 2. Sophie analyzes
analysis = llm.analyze(
    context,
    f"Analyze this error: {error.traceback}"
)

# 3. Sophie creates GitHub issue
issue = github.create_issue(
    context,
    owner="ShotyCZ",
    repo="sophia",
    title=f"Bug: {analysis.summary}",
    body=f"""
    ## Error
    {error.message}
    
    ## Analysis
    {analysis.root_cause}
    
    ## Proposed Fix
    {analysis.solution}
    
    ## Auto-detected by Sophie
    This issue was autonomously identified and reported.
    """,
    labels=["bug", "auto-detected"]
)

# 4. Sophie decides if she can fix autonomously
if analysis.complexity == "simple":
    # 5. Delegate to Jules
    session = jules.create_session(
        context,
        source="sources/github/ShotyCZ/sophia",
        prompt=f"Fix bug in issue #{issue.number}: {analysis.solution}"
    )
    
    # 6. Monitor
    monitor.start_monitoring(context, session.name)
    
    # 7. When complete, create PR
    # 8. Run tests
    # 9. Merge if all green
    
else:
    # Escalate to human
    github.add_comment(
        context,
        issue_number=issue.number,
        body="⚠️ This bug is too complex for autonomous fix. Human review required."
    )
```

## 🎓 Sophie's Decision Making

### When to Delegate to Jules

✅ **Good candidates:**
- New plugin development
- Bug fixes with clear solution
- Test suite creation
- Documentation updates
- Refactoring

❌ **Not suitable:**
- Architecture changes
- Security-critical code
- Database migrations
- Breaking changes

### When to Escalate to Human

Sophie should create issue for human when:
- Tests fail after Jules implementation
- Security implications unclear
- Performance degradation detected
- Breaking API changes needed
- Jules session fails repeatedly

### When to Auto-Merge

Sophie can auto-merge when:
- ✅ All tests passing
- ✅ No security vulnerabilities detected
- ✅ Performance metrics acceptable
- ✅ Code coverage maintained
- ✅ No breaking changes

## 📈 Monitoring Progress

Sophie tracks her autonomous work:

```python
# Get summary
summary = performance_monitor.get_summary(
    context,
    hours=24
)

print(f"""
Sophie's Last 24 Hours:
- Jules delegations: {summary.jules_sessions}
- Successful: {summary.jules_success_rate}%
- PRs created: {summary.prs_created}
- PRs merged: {summary.prs_merged}
- Issues created: {summary.issues_created}
- Cost: ${summary.total_cost}
""")
```

## 🔒 Safety Guardrails

### 1. Cost Limits

```python
# Check before delegating
if performance_monitor.daily_cost > MAX_DAILY_COST:
    github.create_issue(
        context,
        title="⚠️ Daily cost limit reached",
        body="Sophie paused autonomous operations. Please review.",
        labels=["budget-alert"]
    )
    return
```

### 2. Test Requirements

```python
# Never merge without tests
if test_result.exit_code != 0:
    context.logger.error("Tests failed - PR created but not merged")
    github.add_comment(
        context,
        pr_number=pr.number,
        body="⚠️ Tests failing. Manual review required."
    )
```

### 3. Human Approval for Critical Changes

```python
CRITICAL_FILES = [
    "core/kernel.py",
    "core/context.py",
    "config/settings.yaml"
]

if any(f in changed_files for f in CRITICAL_FILES):
    # Require human review
    pr.add_label("needs-human-review")
    context.logger.info("Critical file changed - requiring human approval")
```

## 🚀 Next Steps

Sophie's roadmap for autonomous improvement:

1. **✅ DONE:** GitHub integration
2. **✅ DONE:** Jules monitoring
3. **🔄 NEXT:** Test full workflow end-to-end
4. **📋 PLANNED:** Auto-testing and validation
5. **📋 PLANNED:** Security scanning integration
6. **📋 PLANNED:** Performance regression detection
7. **📋 PLANNED:** Automated dependency updates
8. **📋 PLANNED:** Self-optimization based on metrics

## 📞 Support

If Sophie encounters issues, she will:
1. Log detailed error information
2. Create GitHub issue with context
3. Notify via configured channels
4. Wait for human intervention

Humans can review:
- Sophie's logs: `logs/sophia.log`
- Performance metrics: `data/performance_metrics.db`
- GitHub issues: https://github.com/ShotyCZ/sophia/issues
- Jules sessions: Via Jules API dashboard

---

**Sophie is now ready to improve herself autonomously! 🎉**

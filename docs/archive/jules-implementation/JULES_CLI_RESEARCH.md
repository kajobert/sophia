# Jules CLI Research & Integration Strategy

**Date:** November 3, 2025  
**Purpose:** Research Jules CLI capabilities to solve PR submission blocker in Sophie's autonomous workflow  
**Critical Problem:** Jules API completes sessions (state=COMPLETED) but requires manual "Submit the change" button click to create GitHub PR

---

## 📋 **Executive Summary**

### Critical Discovery from Changelog:
> **"You're now in full control of when your code gets to GitHub. No need to wait for a task to finish or ask Jules to do it for you."**

This strongly suggests Jules CLI provides **programmatic control over PR submission**, potentially solving our autonomous workflow blocker.

---

## 🔍 **What is Jules CLI?**

**Official Name:** Jules Tools  
**Package:** `@google/jules` (NPM)  
**Version:** 0.1.38 (as of October 2025)  
**Installation:** `npm install -g @google/jules`

### Description:
Jules CLI is a lightweight command-line interface for interacting with Google's Jules asynchronous coding agent. It allows developers to:
- Work with Jules directly from terminal (no browser required)
- Create and manage remote coding sessions
- Monitor task progress in real-time
- Script and automate Jules tasks
- Integrate Jules into CI/CD pipelines

---

## 🛠️ **Core CLI Commands**

### Authentication:
```bash
jules login   # Connect to Google account and link GitHub repos
jules logout  # Disconnect authentication
```

### Remote Session Management:
```bash
jules remote new --repo <owner/repo> --session "<task description>"
# Creates new remote session in cloud VM
# Jules clones code, installs deps, makes changes, runs tests

jules remote list
# Lists all active and completed sessions

jules remote list --task
# Lists sessions filtered by task status

# Unknown (need to verify):
jules remote submit <session-id>  # HYPOTHESIS: Triggers PR submission
jules remote status <session-id>   # HYPOTHESIS: Check session state
```

### Interactive Mode:
```bash
jules
# Launches Terminal User Interface (TUI)
# Visual dashboard for managing sessions
```

### Version Check:
```bash
jules --version  # Shows currently installed CLI version
```

---

## 🎯 **Key Features for Sophie Integration**

### 1. **Scriptable & Automatable**
- CLI designed to be composed with other command-line tools
- Can be integrated into existing workflows
- Supports reading tasks from files (e.g., TODO lists)
- Perfect for Sophie's `tool_bash` plugin

### 2. **Asynchronous Execution**
- Tasks run in background cloud VMs
- No need to wait for completion
- Jules reports back when done
- Aligns perfectly with Sophie's monitoring workflow

### 3. **CI/CD Integration**
- Explicitly designed for integration into:
  - GitHub Actions
  - CI pipelines
  - Slack bots
  - Custom automation systems

### 4. **Programmatic Control**
- Full command-line control over task lifecycle
- Scriptable session creation and monitoring
- **POTENTIAL:** Programmatic PR submission (needs verification)

---

## 💡 **Potential Solution for Sophie's Workflow**

### Current Blocker:
```
Sophie → Jules API: create_session()
Jules: state = COMPLETED ✅
[MANUAL STEP REQUIRED] Click "Submit the change" in UI ❌
GitHub PR: Created 
```

### Proposed Solution with CLI:
```bash
# Step 1: Sophie creates Jules session via API (existing implementation)
sophie → tool_jules.create_session(prompt, source, branch)
  → session_id = "sessions/abc123"

# Step 2: Sophie monitors until COMPLETED (existing implementation)
sophie → cognitive_jules_monitor.monitor_until_completion(session_id)
  → state = "COMPLETED"

# Step 3: Sophie triggers PR submission via CLI (NEW CAPABILITY)
sophie → tool_bash.execute("jules remote submit sessions/abc123")
  → GitHub PR created automatically

# Step 4: Sophie reviews and merges (existing GitHub integration)
sophie → tool_github.list_pull_requests()
sophie → tool_github.merge_pull_request()
```

---

## 🚀 **Integration Plan for Sophie**

### Phase 1: Verification & Testing
1. **Install Jules CLI in dev container:**
   ```bash
   npm install -g @google/jules
   ```

2. **Authenticate with Google/GitHub:**
   ```bash
   jules login
   ```

3. **Test basic commands:**
   ```bash
   jules remote list
   jules --help
   jules remote --help
   ```

4. **Research exact PR submission command:**
   - Check official docs: https://jules.google/docs/cli/reference
   - Test with real session
   - Verify command syntax

### Phase 2: Plugin Enhancement
1. **Update `plugins/tool_jules.py`:**
   - Add method: `submit_session_pr_via_cli(session_id)`
   - Use `tool_bash` to execute Jules CLI commands
   - Parse CLI output for success/failure
   - Return structured response

2. **Example Implementation:**
   ```python
   def submit_session_pr_via_cli(self, context, session_id):
       """
       Submit completed Jules session as GitHub PR using Jules CLI.
       
       Args:
           session_id: Jules session ID (format: "sessions/abc123")
       
       Returns:
           Success/failure status with PR details
       """
       # Execute Jules CLI command via bash
       bash_tool = context.get_plugin("tool_bash")
       result = bash_tool.execute(
           context, 
           command=f"jules remote submit {session_id}"
       )
       
       # Parse output and return structured response
       if "Pull request created" in result.output:
           return {
               "success": True,
               "message": "PR submitted successfully via Jules CLI",
               "session_id": session_id
           }
       else:
           return {
               "success": False,
               "error": result.output,
               "session_id": session_id
           }
   ```

### Phase 3: Workflow Integration
1. **Update `cognitive_jules_monitor.py`:**
   - After detecting COMPLETED state
   - Automatically trigger CLI PR submission
   - Wait for PR creation confirmation
   - Return PR URL for Sophie's review

2. **Update autonomous workflow:**
   ```python
   # Current flow:
   1. create_session → session_id
   2. monitor_until_completion → COMPLETED
   3. [BLOCKED - manual intervention needed]
   
   # New flow with CLI:
   1. create_session → session_id
   2. monitor_until_completion → COMPLETED
   3. submit_session_pr_via_cli → PR created ✅
   4. list_pull_requests → find PR
   5. review & merge → autonomous completion ✅
   ```

### Phase 4: Configuration
1. **Add to `config/settings.yaml`:**
   ```yaml
   tool_jules:
     api_key: "${JULES_API_KEY}"
     cli_enabled: true  # NEW: Enable CLI integration
     cli_auto_submit: true  # NEW: Auto-submit PRs after completion
     cli_path: "/usr/local/bin/jules"  # NEW: Path to CLI binary
   ```

2. **Add to `.env.example`:**
   ```bash
   # Jules CLI integration
   JULES_CLI_ENABLED=true
   JULES_CLI_AUTO_SUBMIT=true
   ```

---

## 📊 **Benefits for Sophie's Autonomy**

### Before (API Only):
- ❌ Manual intervention required for PR submission
- ❌ Breaks autonomous workflow
- ❌ Requires human to click button in UI
- ⚠️ Sophie cannot complete full self-improvement cycle

### After (API + CLI):
- ✅ **Fully autonomous PR submission**
- ✅ **Complete workflow automation:** Research → Delegate → Monitor → Submit → Review → Merge
- ✅ **No human intervention** until final master merge approval
- ✅ **Sophie can work in her own branch** (sophie/autonomous-dev)
- ✅ **CI/CD integration** possible for advanced workflows

---

## 🔬 **Research Questions (Need Verification)**

### High Priority:
1. **Does `jules remote submit <session-id>` command exist?**
   - If not, what's the exact command syntax?
   - Alternative: `jules remote approve`, `jules remote push`, etc.?

2. **What's the CLI output format?**
   - JSON for easy parsing?
   - Plain text that needs regex?
   - Exit codes for success/failure?

3. **Does CLI require interactive confirmation?**
   - Can it run in non-interactive mode for scripts?
   - Flags like `--yes` or `--no-confirm`?

### Medium Priority:
4. **Authentication persistence:**
   - Does `jules login` persist credentials?
   - Does it work in Docker containers?
   - Token-based auth available?

5. **Error handling:**
   - What errors can CLI return?
   - Network failures?
   - Invalid session IDs?
   - GitHub permission issues?

### Low Priority:
6. **Advanced features:**
   - Can CLI create sessions (alternative to API)?
   - Monitoring via CLI vs API?
   - PR customization (title, body, labels)?

---

## 📖 **Resources**

### Official Documentation:
- **CLI Reference:** https://jules.google/docs/cli/reference
- **Changelog:** https://jules.google/docs/changelog
- **API Docs:** https://developers.google.com/jules/api
- **Blog Post:** https://blog.google/technology/google-labs/jules-tools-jules-api/
- **Dev Blog:** https://developers.googleblog.com/en/meet-jules-tools-a-command-line-companion-for-googles-async-coding-agent/

### NPM Package:
- **Package:** https://www.npmjs.com/package/@google/jules
- **Current Version:** 0.1.38 (updated 4 days ago as of Nov 2025)
- **Install:** `npm install -g @google/jules`

### Community Resources:
- **Practical Examples:** https://jules.google/docs/cli/examples
- **Integration Guide:** https://skywork.ai/blog/jules-cli-hands-on-integrating-google-ai-assistant-into-terminal-and-ci/

---

## 🎬 **Next Steps**

### Immediate Actions:
1. ✅ **Research completed** - Jules CLI capabilities documented
2. 🔄 **Install Jules CLI** in Sophie's dev container
3. 🔄 **Authenticate** and test basic commands
4. 🔄 **Verify PR submission** command exists and works
5. 🔄 **Document exact syntax** and output format

### Short Term (This Week):
- Implement `submit_session_pr_via_cli()` in `tool_jules.py`
- Test end-to-end workflow with CLI integration
- Update `cognitive_jules_monitor` to use CLI for PR submission
- Document new workflow in `AUTONOMOUS_WORKFLOW_GUIDE.md`

### Medium Term (Next Sprint):
- Implement branch strategy (sophie/autonomous-dev)
- Add comprehensive error handling for CLI failures
- Create cognitive_sophie_autonomy orchestrator plugin
- Full autonomous workflow testing

---

## ⚠️ **Risk Assessment**

### Low Risk:
- CLI is officially supported by Google
- Actively maintained (last update 4 days ago)
- Designed for automation and scripting

### Medium Risk:
- PR submission command might not exist (needs verification)
- CLI might require interactive confirmation
- Authentication in Docker might be tricky

### Mitigation Strategies:
- **Fallback 1:** If CLI doesn't support PR submission, create GitHub issue to notify human
- **Fallback 2:** Use Jules TUI in headless mode if available
- **Fallback 3:** Contact Jules team for official support/feature request

---

## 💬 **Conclusion**

Jules CLI represents a **highly promising solution** to Sophie's autonomous workflow blocker. The changelog statement "You're now in full control of when your code gets to GitHub" strongly suggests programmatic PR control is available.

**Confidence Level:** **HIGH (80%)**
- CLI is designed for automation ✅
- Explicitly supports scripting ✅
- Intended for CI/CD integration ✅
- Recent updates show active development ✅

**Next Critical Step:** Install and test Jules CLI to verify exact PR submission syntax.

---

**Research Conducted By:** GitHub Copilot (VS Code Assistant)  
**Research Method:** Web search using `vscode-websearchforcopilot_webSearch` tool  
**Sources:** Official Google documentation, developer blogs, NPM registry  
**Confidence:** High - based on official sources and recent documentation

"""
Safe Integrator Plugin - INSTINCTS Layer (Reptilian Brain)

HKA Layer: INSTINCTS
Purpose: Atomic integration with rollback capabilities - protect system from harm
Philosophy: All or nothing - no partial states

According to 02_COGNITIVE_ARCHITECTURE.md:
"Reptilian Brain - reflexive protection and safety mechanisms"

According to 01_VISION_AND_DNA.md:
"Ahimsa (Non-Harm) - Never damage existing functionality, always have rollback capability"
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from enum import Enum, auto

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class IntegrationStatus(Enum):
    """Status of integration process."""
    PENDING = auto()
    BACKING_UP = auto()
    WRITING_FILES = auto()
    TESTING = auto()
    COMMITTING = auto()
    SUCCESS = auto()
    FAILED = auto()
    ROLLED_BACK = auto()


class SafeIntegrator(BasePlugin):
    """
    Safe Integrator - Instinctive atomic integration with rollback.
    
    Provides:
    - Pre-integration backups (Git tags)
    - Atomic operations (all or nothing)
    - Full test suite validation
    - Automatic rollback on failure
    - Integration history tracking
    
    HKA Layer: INSTINCTS (Reptilian Brain)
    Response Time: Immediate rollback on failure
    Philosophy: Ahimsa - Never harm the system
    """

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._git_tool: Optional[BasePlugin] = None
        self._bash_tool: Optional[BasePlugin] = None
        self._file_system_tool: Optional[BasePlugin] = None
        
        # Configuration
        self._backup_dir: Path = Path("data/backups")
        self._auto_rollback: bool = True
        self._require_tests_pass: bool = True
        self._backup_retention_days: int = 30

    @property
    def name(self) -> str:
        return "cognitive_integrator"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """
        Initialize Safe Integrator plugin.
        
        Args:
            config: Configuration dictionary with:
                - tool_git: Reference to Git tool
                - tool_bash: Reference to Bash tool for test execution
                - tool_file_system: Reference to file system tool
                - backup_dir: Directory for backup metadata (default: data/backups)
                - auto_rollback: Automatic rollback on failure (default: True)
                - require_tests_pass: Require all tests to pass (default: True)
                - backup_retention_days: Days to keep backups (default: 30)
        """
        self._config = config
        
        # Get tool references
        self._git_tool = config.get("tool_git")
        self._bash_tool = config.get("tool_bash")
        self._file_system_tool = config.get("tool_file_system")
        
        # Configuration
        backup_dir_str = config.get("backup_dir", "data/backups")
        self._backup_dir = Path(backup_dir_str)
        self._auto_rollback = config.get("auto_rollback", True)
        self._require_tests_pass = config.get("require_tests_pass", True)
        self._backup_retention_days = config.get("backup_retention_days", 30)
        
        # Ensure backup directory exists
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"SafeIntegrator initialized: backup_dir={self._backup_dir}, "
                   f"auto_rollback={self._auto_rollback}, require_tests_pass={self._require_tests_pass}")

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Execute safe integration operations.
        
        Expected context.payload:
            - action: "integrate_plugin" | "rollback" | "list_backups"
            - plugin_code: str (for integrate_plugin)
            - test_code: str (for integrate_plugin)
            - plugin_name: str (for integrate_plugin)
            - qa_report: dict (for integrate_plugin)
            - backup_id: str (for rollback)
        
        Returns SharedContext with payload:
            - success: bool
            - backup_id: str (for integrate_plugin)
            - message: str
            - test_results: dict (for integrate_plugin)
            - backups: List[dict] (for list_backups)
        """
        action = context.payload.get("action", "integrate_plugin")
        
        if action == "integrate_plugin":
            return await self._integrate_plugin(context)
        elif action == "rollback":
            return await self._rollback(context)
        elif action == "list_backups":
            return await self._list_backups(context)
        else:
            context.payload["error"] = f"Unknown action: {action}"
            return context

    async def _integrate_plugin(self, context: SharedContext) -> SharedContext:
        """
        Perform atomic plugin integration with rollback capability.
        
        Workflow:
        1. Create backup (Git tag)
        2. Write plugin and test files
        3. Run full test suite
        4. If success: commit changes
        5. If failure: rollback to backup
        
        Returns context with integration results.
        """
        plugin_code = context.payload.get("plugin_code", "")
        test_code = context.payload.get("test_code", "")
        plugin_name = context.payload.get("plugin_name", "")
        qa_report = context.payload.get("qa_report", {})
        
        # Validation
        if not plugin_code:
            context.payload["error"] = "No plugin_code provided"
            context.payload["success"] = False
            return context
        
        if not plugin_name:
            context.payload["error"] = "No plugin_name provided"
            context.payload["success"] = False
            return context
        
        backup_id = ""
        integration_status = IntegrationStatus.PENDING
        
        try:
            # Step 1: Create backup
            integration_status = IntegrationStatus.BACKING_UP
            backup_id = await self._create_backup(plugin_name)
            logger.info(f"Backup created: {backup_id}")
            
            # Step 2: Write files
            integration_status = IntegrationStatus.WRITING_FILES
            plugin_path, test_path = await self._write_files(
                plugin_code, test_code, plugin_name
            )
            logger.info(f"Files written: {plugin_path}, {test_path}")
            
            # Step 3: Run full test suite
            integration_status = IntegrationStatus.TESTING
            test_results = await self._run_full_test_suite()
            logger.info(f"Tests completed: passed={test_results.get('passed', False)}")
            
            # Step 4: Verify tests passed
            if self._require_tests_pass and not test_results.get("passed", False):
                raise RuntimeError(f"Tests failed: {test_results.get('summary', 'Unknown error')}")
            
            # Step 5: Commit changes
            integration_status = IntegrationStatus.COMMITTING
            commit_sha = await self._commit_integration(plugin_name, qa_report)
            logger.info(f"Integration committed: {commit_sha}")
            
            integration_status = IntegrationStatus.SUCCESS
            
            # Success response
            context.payload.update({
                "success": True,
                "backup_id": backup_id,
                "message": f"Plugin '{plugin_name}' integrated successfully",
                "test_results": test_results,
                "commit_sha": commit_sha,
                "plugin_path": str(plugin_path),
                "test_path": str(test_path)
            })
            
        except Exception as e:
            integration_status = IntegrationStatus.FAILED
            logger.error(f"Integration failed at {integration_status}: {e}", exc_info=True)
            
            # Automatic rollback
            if self._auto_rollback and backup_id:
                try:
                    await self._rollback_to_backup(backup_id)
                    integration_status = IntegrationStatus.ROLLED_BACK
                    logger.info(f"Rolled back to backup: {backup_id}")
                    
                    context.payload.update({
                        "success": False,
                        "backup_id": backup_id,
                        "message": f"Integration failed and rolled back: {str(e)}",
                        "error": str(e),
                        "rolled_back": True
                    })
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}", exc_info=True)
                    context.payload.update({
                        "success": False,
                        "backup_id": backup_id,
                        "message": f"Integration AND rollback failed!",
                        "error": str(e),
                        "rollback_error": str(rollback_error),
                        "rolled_back": False
                    })
            else:
                context.payload.update({
                    "success": False,
                    "backup_id": backup_id,
                    "message": f"Integration failed: {str(e)}",
                    "error": str(e),
                    "rolled_back": False
                })
        
        return context

    async def _create_backup(self, plugin_name: str) -> str:
        """
        Create Git backup with tag.
        
        Args:
            plugin_name: Name of plugin being integrated
            
        Returns:
            Backup tag name (e.g., backup-20251026-143022-plugin_name)
        """
        if not self._git_tool:
            raise RuntimeError("Git tool not available")
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        tag_name = f"backup-{timestamp}-{plugin_name}"
        
        # Get current repo status
        if hasattr(self._git_tool, 'repo') and self._git_tool.repo:
            repo = self._git_tool.repo
            
            # Check for uncommitted changes
            if repo.is_dirty(untracked_files=True):
                # Add all changes
                repo.git.add(A=True)
                # Commit
                commit_message = f"Pre-integration backup for {plugin_name}"
                repo.index.commit(commit_message)
                logger.info(f"Committed changes: {commit_message}")
            
            # Create tag
            repo.create_tag(tag_name, message=f"Backup before integrating {plugin_name}")
            logger.info(f"Created backup tag: {tag_name}")
            
            # Save backup metadata
            backup_metadata = {
                "tag": tag_name,
                "plugin_name": plugin_name,
                "timestamp": timestamp,
                "commit_sha": str(repo.head.commit.hexsha)
            }
            
            metadata_file = self._backup_dir / f"{tag_name}.json"
            import json
            metadata_file.write_text(json.dumps(backup_metadata, indent=2))
            
            return tag_name
        else:
            raise RuntimeError("Git repository not initialized")

    async def _write_files(
        self,
        plugin_code: str,
        test_code: str,
        plugin_name: str
    ) -> tuple[Path, Path]:
        """
        Write plugin and test files to disk.
        
        Args:
            plugin_code: Plugin source code
            test_code: Test source code
            plugin_name: Name of plugin
            
        Returns:
            Tuple of (plugin_path, test_path)
        """
        # Determine file paths
        plugin_path = Path("plugins") / f"{plugin_name}.py"
        test_path = Path("tests/plugins") / f"test_{plugin_name}.py"
        
        # Write plugin file
        plugin_path.write_text(plugin_code, encoding="utf-8")
        logger.info(f"Written plugin file: {plugin_path}")
        
        # Write test file (if provided)
        if test_code:
            test_path.write_text(test_code, encoding="utf-8")
            logger.info(f"Written test file: {test_path}")
        
        return plugin_path, test_path

    async def _run_full_test_suite(self) -> Dict[str, Any]:
        """
        Run complete test suite to verify no regressions.
        
        Returns:
            Dictionary with test results:
            - passed: bool
            - summary: str
            - output: str
            - total: int
            - failed: int
        """
        if not self._bash_tool:
            raise RuntimeError("Bash tool not available")
        
        # Prepare test command
        test_command = "PYTHONPATH=/workspaces/sophia pytest tests/ -v --tb=line"
        
        # Execute tests via bash tool
        context = SharedContext(
            session_id="integration-test",
            current_state="testing",
            logger=logger
        )
        context.payload = {
            "command": test_command,
            "timeout": 60  # 60 second timeout
        }
        
        result = await self._bash_tool.execute(context)
        
        # Parse test output
        output = result.payload.get("output", "")
        exit_code = result.payload.get("exit_code", 1)
        
        # Extract test summary
        passed = exit_code == 0
        
        # Try to extract test counts from pytest output
        import re
        summary_match = re.search(r'(\d+) passed', output)
        failed_match = re.search(r'(\d+) failed', output)
        
        total = int(summary_match.group(1)) if summary_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        
        return {
            "passed": passed,
            "summary": f"{total} passed" + (f", {failed} failed" if failed > 0 else ""),
            "output": output,
            "total": total,
            "failed": failed
        }

    async def _commit_integration(self, plugin_name: str, qa_report: dict) -> str:
        """
        Commit integrated plugin to Git.
        
        Args:
            plugin_name: Name of plugin
            qa_report: QA validation report
            
        Returns:
            Commit SHA
        """
        if not self._git_tool:
            raise RuntimeError("Git tool not available")
        
        if hasattr(self._git_tool, 'repo') and self._git_tool.repo:
            repo = self._git_tool.repo
            
            # Add files
            repo.git.add(A=True)
            
            # Create commit message
            compliance_score = qa_report.get("compliance_score", 0.0)
            commit_message = f"feat: Auto-integrate plugin {plugin_name}\n\n"
            commit_message += f"QA compliance score: {compliance_score:.2f}\n"
            commit_message += f"Integrated via SafeIntegrator (INSTINCTS layer)\n"
            
            # Commit
            commit = repo.index.commit(commit_message)
            commit_sha = str(commit.hexsha)
            
            logger.info(f"Committed integration: {commit_sha}")
            return commit_sha
        else:
            raise RuntimeError("Git repository not initialized")

    async def _rollback(self, context: SharedContext) -> SharedContext:
        """
        Rollback to a specific backup.
        
        Expected payload:
            - backup_id: str (tag name)
            
        Returns context with rollback results.
        """
        backup_id = context.payload.get("backup_id", "")
        
        if not backup_id:
            context.payload["error"] = "No backup_id provided"
            context.payload["success"] = False
            return context
        
        try:
            await self._rollback_to_backup(backup_id)
            context.payload.update({
                "success": True,
                "message": f"Rolled back to {backup_id}"
            })
        except Exception as e:
            logger.error(f"Rollback failed: {e}", exc_info=True)
            context.payload.update({
                "success": False,
                "error": str(e),
                "message": f"Rollback failed: {str(e)}"
            })
        
        return context

    async def _rollback_to_backup(self, backup_id: str) -> None:
        """
        Perform Git rollback to backup tag.
        
        Args:
            backup_id: Backup tag name
        """
        if not self._git_tool:
            raise RuntimeError("Git tool not available")
        
        if hasattr(self._git_tool, 'repo') and self._git_tool.repo:
            repo = self._git_tool.repo
            
            # Verify tag exists - check tag names, not tag objects
            tag_names = [tag.name for tag in repo.tags]
            if backup_id not in tag_names:
                raise ValueError(f"Backup tag not found: {backup_id}")
            
            # Reset to tag
            repo.git.reset('--hard', backup_id)
            logger.info(f"Reset to backup: {backup_id}")
            
            # Clean untracked files
            repo.git.clean('-fd')
            logger.info("Cleaned untracked files")
        else:
            raise RuntimeError("Git repository not initialized")

    async def _list_backups(self, context: SharedContext) -> SharedContext:
        """
        List all available backups.
        
        Returns context with backup list.
        """
        try:
            backups: List[Dict[str, Any]] = []
            
            # Read metadata files
            if self._backup_dir.exists():
                import json
                for metadata_file in sorted(self._backup_dir.glob("backup-*.json")):
                    try:
                        metadata = json.loads(metadata_file.read_text())
                        backups.append(metadata)
                    except Exception as e:
                        logger.warning(f"Failed to read backup metadata {metadata_file}: {e}")
            
            # Also check Git tags
            if self._git_tool and hasattr(self._git_tool, 'repo') and self._git_tool.repo:
                repo = self._git_tool.repo
                for tag in repo.tags:
                    if tag.name.startswith("backup-"):
                        # Check if already in backups list
                        if not any(b.get("tag") == tag.name for b in backups):
                            backups.append({
                                "tag": tag.name,
                                "plugin_name": "unknown",
                                "timestamp": tag.name.split("-")[1] if len(tag.name.split("-")) > 1 else "unknown",
                                "commit_sha": str(tag.commit.hexsha)
                            })
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda b: b.get("timestamp", ""), reverse=True)
            
            context.payload.update({
                "success": True,
                "backups": backups,
                "count": len(backups)
            })
        except Exception as e:
            logger.error(f"Failed to list backups: {e}", exc_info=True)
            context.payload.update({
                "success": False,
                "error": str(e),
                "backups": []
            })
        
        return context

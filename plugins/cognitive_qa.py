"""
Quality Assurance Plugin - INSTINCTS Layer (Reptilian Brain)

HKA Layer: INSTINCTS
Purpose: Reflexive multi-level code validation before integration
Philosophy: Fast, deterministic safety checks + deep LLM review

According to 02_COGNITIVE_ARCHITECTURE.md:
"Reptilian Brain - reflexive filtering and protection, responds in < 1s"

According to 01_VISION_AND_DNA.md:
"Ahimsa (Non-Harm) - Never damage existing functionality"
"""

import ast
import re
from typing import Dict, List, Optional, Any
from enum import Enum, auto
from pathlib import Path

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext


class ValidationLevel(Enum):
    """Validation severity levels."""
    ERROR = auto()      # Blocking issue - must fix
    WARNING = auto()    # Should fix, but not blocking
    INFO = auto()       # Suggestion for improvement


class ValidationCategory(Enum):
    """Categories of validation issues."""
    ARCHITECTURE = auto()   # Core-Plugin violations, BasePlugin contract
    QUALITY = auto()        # Type hints, docstrings, style
    SAFETY = auto()         # Security, core/ modifications
    TESTING = auto()        # Test coverage, test quality
    LANGUAGE = auto()       # English-only requirement


class QualityAssurance(BasePlugin):
    """
    Quality Assurance - Instinctive multi-level code validation.
    
    Performs 4-level validation:
    1. REFLEX: Fast deterministic rules (< 100ms)
    2. STATIC: AST-based structural analysis
    3. LLM: Deep semantic review
    4. EXECUTION: Test execution in sandbox (optional)
    
    HKA Layer: INSTINCTS (Reptilian Brain)
    Response Time: Level 1-2 < 1s, Level 3 < 10s
    """

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._llm_tool: Optional[BasePlugin] = None
        self._file_system_tool: Optional[BasePlugin] = None
        self._bash_tool: Optional[BasePlugin] = None
        
        # Validation thresholds
        self._min_compliance_score: float = 0.80
        self._allow_warnings: bool = True
        self._require_tests: bool = True

    @property
    def name(self) -> str:
        return "cognitive_qa"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """
        Initialize Quality Assurance plugin.
        
        Args:
            config: Configuration dictionary with:
                - min_compliance_score: Minimum score to approve (0.0-1.0)
                - allow_warnings: Allow integration with warnings
                - require_tests: Require test file
                - tool_llm: Reference to LLM tool for deep review
                - tool_file_system: Reference to file system tool
                - tool_bash: Reference to bash tool for test execution
        """
        self._config = config
        
        # Get tool references
        self._llm_tool = config.get("tool_llm")
        self._file_system_tool = config.get("tool_file_system")
        self._bash_tool = config.get("tool_bash")
        
        # Configuration
        self._min_compliance_score = config.get("min_compliance_score", 0.80)
        self._allow_warnings = config.get("allow_warnings", True)
        self._require_tests = config.get("require_tests", True)

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Execute quality assurance validation.
        
        Expected context.payload:
            - action: "review_code"
            - plugin_code: str (source code to review)
            - test_code: str (test code to review)
            - plugin_name: str (name of the plugin)
            - specification: str (original spec for context)
        
        Returns SharedContext with payload:
            - approved: bool
            - issues: List[dict]
            - compliance_score: float (0.0-1.0)
            - must_fix: List[str] (blocking issues)
            - suggestions: List[str] (improvements)
        """
        action = context.payload.get("action", "review_code")
        
        if action == "review_code":
            return await self._review_code(context)
        else:
            context.payload["error"] = f"Unknown action: {action}"
            return context

    async def _review_code(self, context: SharedContext) -> SharedContext:
        """
        Perform complete multi-level code review.
        
        Returns context with review results in payload.
        """
        plugin_code = context.payload.get("plugin_code", "")
        test_code = context.payload.get("test_code", "")
        plugin_name = context.payload.get("plugin_name", "unknown")
        specification = context.payload.get("specification", "")
        
        if not plugin_code:
            context.payload["error"] = "No plugin_code provided"
            return context
        
        all_issues: List[Dict[str, Any]] = []
        
        # LEVEL 1: Reflexive checks (fast)
        reflex_issues = await self._reflex_checks(plugin_code, test_code)
        all_issues.extend(reflex_issues)
        
        # LEVEL 2: Static analysis (AST)
        static_issues = await self._architecture_compliance(plugin_code)
        all_issues.extend(static_issues)
        
        # LEVEL 3: LLM deep review (if available)
        if self._llm_tool:
            llm_issues = await self._llm_deep_review(plugin_code, test_code, specification)
            all_issues.extend(llm_issues)
        
        # LEVEL 4: Test execution (optional - not in this iteration)
        # execution_issues = await self._execute_tests(plugin_code, test_code, plugin_name)
        
        # Calculate compliance score
        compliance_score = self._calculate_compliance_score(all_issues)
        
        # Determine approval
        must_fix = [
            issue["message"] for issue in all_issues
            if issue["level"] == ValidationLevel.ERROR
        ]
        
        approved = (
            compliance_score >= self._min_compliance_score and
            len(must_fix) == 0
        )
        
        if not self._allow_warnings:
            warnings = [i for i in all_issues if i["level"] == ValidationLevel.WARNING]
            if warnings:
                approved = False
        
        # Build suggestions
        suggestions = [
            issue["suggestion"] for issue in all_issues
            if issue.get("suggestion") and issue["level"] != ValidationLevel.ERROR
        ]
        
        # Update context
        context.payload.update({
            "approved": approved,
            "issues": all_issues,
            "compliance_score": compliance_score,
            "must_fix": must_fix,
            "suggestions": suggestions
        })
        
        return context

    async def _reflex_checks(self, plugin_code: str, test_code: str) -> List[Dict[str, Any]]:
        """
        LEVEL 1: Fast reflexive validation rules.
        
        Checks:
        - BasePlugin inheritance
        - Required properties (name, plugin_type, version)
        - Required methods (setup, execute)
        - English-only code
        - No core/ modifications
        - No dangerous operations
        
        Returns list of issues.
        """
        issues: List[Dict[str, Any]] = []
        
        # Check 1: BasePlugin inheritance
        if "class" in plugin_code and "BasePlugin" not in plugin_code:
            issues.append({
                "level": ValidationLevel.ERROR,
                "category": ValidationCategory.ARCHITECTURE,
                "message": "Plugin class must inherit from BasePlugin",
                "suggestion": "Add '(BasePlugin)' to class definition"
            })
        
        # Check 2: Required properties present
        required_properties = ["@property", "def name", "def plugin_type", "def version"]
        for prop in required_properties:
            if prop not in plugin_code:
                issues.append({
                    "level": ValidationLevel.ERROR,
                    "category": ValidationCategory.ARCHITECTURE,
                    "message": f"Missing required property/decorator: {prop}",
                    "suggestion": "Implement all required BasePlugin properties"
                })
        
        # Check 3: Required methods
        if "def setup(self" not in plugin_code:
            issues.append({
                "level": ValidationLevel.ERROR,
                "category": ValidationCategory.ARCHITECTURE,
                "message": "Missing required method: setup()",
                "suggestion": "Implement setup(self, config: dict) method"
            })
        
        if "async def execute(self" not in plugin_code and "def execute(self" not in plugin_code:
            issues.append({
                "level": ValidationLevel.ERROR,
                "category": ValidationCategory.ARCHITECTURE,
                "message": "Missing required method: execute()",
                "suggestion": "Implement async def execute(self, context: SharedContext) method"
            })
        
        # Check 4: No core/ modifications (security)
        if "core/" in plugin_code or "core\\" in plugin_code:
            issues.append({
                "level": ValidationLevel.ERROR,
                "category": ValidationCategory.SAFETY,
                "message": "Plugin attempts to modify core/ - FORBIDDEN",
                "suggestion": "Remove all references to core/ directory"
            })
        
        # Check 5: No base_plugin.py modifications
        if "base_plugin.py" in plugin_code:
            issues.append({
                "level": ValidationLevel.ERROR,
                "category": ValidationCategory.SAFETY,
                "message": "Plugin attempts to modify base_plugin.py - FORBIDDEN",
                "suggestion": "Never modify base_plugin.py"
            })
        
        # Check 6: Dangerous operations check
        dangerous_patterns = [
            (r'\beval\s*\(', "Use of eval() detected - security risk"),
            (r'\bexec\s*\(', "Use of exec() detected - security risk"),
            (r'__import__\s*\(', "Dynamic import detected - potential security risk"),
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, plugin_code):
                issues.append({
                    "level": ValidationLevel.WARNING,
                    "category": ValidationCategory.SAFETY,
                    "message": message,
                    "suggestion": "Avoid dynamic code execution, use safer alternatives"
                })
        
        # Check 7: Test file required
        if self._require_tests and not test_code:
            issues.append({
                "level": ValidationLevel.ERROR,
                "category": ValidationCategory.TESTING,
                "message": "No test code provided",
                "suggestion": "Create comprehensive test file with >80% coverage"
            })
        
        # Check 8: Czech/non-English text detection (basic)
        czech_chars = re.compile(r'[áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]')
        if czech_chars.search(plugin_code):
            issues.append({
                "level": ValidationLevel.ERROR,
                "category": ValidationCategory.LANGUAGE,
                "message": "Non-English characters detected in code",
                "suggestion": "All code must be in English (comments, docstrings, variables)"
            })
        
        return issues

    async def _architecture_compliance(self, plugin_code: str) -> List[Dict[str, Any]]:
        """
        LEVEL 2: Static analysis using AST parsing.
        
        Checks:
        - Type hints on all functions
        - Docstrings on all classes and functions
        - Google-style docstrings
        - Correct BasePlugin contract implementation
        
        Returns list of issues.
        """
        issues: List[Dict[str, Any]] = []
        
        try:
            tree = ast.parse(plugin_code)
        except SyntaxError as e:
            issues.append({
                "level": ValidationLevel.ERROR,
                "category": ValidationCategory.QUALITY,
                "message": f"Syntax error in code: {e}",
                "suggestion": "Fix syntax errors before submission"
            })
            return issues
        
        # Analyze all function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                func_name = node.name
                
                # Check for docstring
                docstring = ast.get_docstring(node)
                if not docstring:
                    issues.append({
                        "level": ValidationLevel.WARNING,
                        "category": ValidationCategory.QUALITY,
                        "message": f"Function '{func_name}' missing docstring",
                        "suggestion": "Add Google-style docstring describing purpose, args, returns"
                    })
                
                # Check for type hints on arguments and return
                has_return_annotation = node.returns is not None
                
                # Skip 'self' and 'cls' when counting args
                args_to_check = [
                    arg for arg in node.args.args
                    if arg.arg not in ['self', 'cls']
                ]
                
                missing_annotations = [
                    arg.arg for arg in args_to_check
                    if arg.annotation is None
                ]
                
                if missing_annotations:
                    issues.append({
                        "level": ValidationLevel.WARNING,
                        "category": ValidationCategory.QUALITY,
                        "message": f"Function '{func_name}' has arguments without type hints: {missing_annotations}",
                        "suggestion": "Add type annotations to all function arguments"
                    })
                
                # Check return type (except for __init__ and setup which can be -> None)
                if not has_return_annotation and func_name not in ['__init__', 'setup']:
                    issues.append({
                        "level": ValidationLevel.WARNING,
                        "category": ValidationCategory.QUALITY,
                        "message": f"Function '{func_name}' missing return type annotation",
                        "suggestion": "Add return type annotation (-> Type)"
                    })
            
            # Check class definitions
            if isinstance(node, ast.ClassDef):
                class_docstring = ast.get_docstring(node)
                if not class_docstring:
                    issues.append({
                        "level": ValidationLevel.WARNING,
                        "category": ValidationCategory.QUALITY,
                        "message": f"Class '{node.name}' missing docstring",
                        "suggestion": "Add comprehensive class docstring"
                    })
        
        return issues

    async def _llm_deep_review(
        self,
        plugin_code: str,
        test_code: str,
        specification: str
    ) -> List[Dict[str, Any]]:
        """
        LEVEL 3: Deep semantic review using LLM.
        
        Uses LLM to analyze:
        - Code quality and best practices
        - Anti-pattern detection
        - Logic correctness
        - Test adequacy
        - Specification alignment
        
        Returns list of issues.
        """
        issues: List[Dict[str, Any]] = []
        
        if not self._llm_tool:
            return issues
        
        review_prompt = f"""You are a senior Python code reviewer. Review this plugin code for quality and compliance.

SPECIFICATION:
{specification}

PLUGIN CODE:
```python
{plugin_code}
```

TEST CODE:
```python
{test_code}
```

Review for:
1. Code quality (readability, maintainability, best practices)
2. Anti-patterns or code smells
3. Logic correctness and edge cases
4. Test coverage and quality
5. Alignment with specification

Provide feedback in this JSON format:
{{
  "issues": [
    {{
      "level": "error|warning|info",
      "category": "quality|testing|logic",
      "message": "specific issue description",
      "suggestion": "how to fix it"
    }}
  ]
}}

Be concise and actionable. Focus on significant issues only.
"""
        
        try:
            # Call LLM tool
            llm_context = SharedContext()
            llm_context.payload = {
                "action": "generate",
                "prompt": review_prompt,
                "max_tokens": 1000,
                "temperature": 0.3  # Low temperature for consistency
            }
            
            result = await self._llm_tool.execute(llm_context)
            llm_response = result.payload.get("response", "")
            
            # Parse LLM response (basic JSON extraction)
            import json
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                try:
                    review_data = json.loads(json_match.group(0))
                    llm_issues = review_data.get("issues", [])
                    
                    # Convert to our issue format
                    for issue in llm_issues:
                        level_str = issue.get("level", "info").upper()
                        category_str = issue.get("category", "quality").upper()
                        
                        # Map strings to enums
                        level_map = {
                            "ERROR": ValidationLevel.ERROR,
                            "WARNING": ValidationLevel.WARNING,
                            "INFO": ValidationLevel.INFO
                        }
                        category_map = {
                            "QUALITY": ValidationCategory.QUALITY,
                            "TESTING": ValidationCategory.TESTING,
                            "SAFETY": ValidationCategory.SAFETY,
                            "ARCHITECTURE": ValidationCategory.ARCHITECTURE
                        }
                        
                        issues.append({
                            "level": level_map.get(level_str, ValidationLevel.INFO),
                            "category": category_map.get(category_str, ValidationCategory.QUALITY),
                            "message": issue.get("message", ""),
                            "suggestion": issue.get("suggestion", "")
                        })
                except json.JSONDecodeError:
                    pass  # Ignore if JSON parsing fails
        
        except Exception as e:
            # LLM review is optional, don't fail if it errors
            issues.append({
                "level": ValidationLevel.INFO,
                "category": ValidationCategory.QUALITY,
                "message": f"LLM review unavailable: {str(e)}",
                "suggestion": "Manual review recommended"
            })
        
        return issues

    def _calculate_compliance_score(self, issues: List[Dict[str, Any]]) -> float:
        """
        Calculate overall compliance score from issues.
        
        Scoring:
        - Start at 1.0 (perfect)
        - ERROR: -0.20 each
        - WARNING: -0.05 each
        - INFO: -0.01 each
        - Minimum: 0.0
        
        Returns float 0.0-1.0
        """
        score = 1.0
        
        for issue in issues:
            level = issue["level"]
            if level == ValidationLevel.ERROR:
                score -= 0.20
            elif level == ValidationLevel.WARNING:
                score -= 0.05
            elif level == ValidationLevel.INFO:
                score -= 0.01
        
        return max(0.0, score)

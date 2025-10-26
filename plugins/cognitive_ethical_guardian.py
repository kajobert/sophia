"""
Cognitive Ethical Guardian Plugin

Instinctive ethical and safety validation.
Respects HKA: INSTINCTS layer - reflexive filtering and protection.

DNA Principles Enforcement:
- Ahimsa (Non-harm): Reflexively blocks harmful goals and unsafe code
- Satya (Truth): Validates transparency and honesty in goals
- Kaizen (Continuous Improvement): Ensures goals support growth and learning
"""

import logging
import re
from typing import Dict, List, Any
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class EthicalGuardian(BasePlugin):
    """
    Instinctive ethical validation - first line of defense.
    HKA Layer: INSTINCTS (Reptilian Brain)
    
    Reflexive validation rules:
    1. DNA compliance check (Ahimsa, Satya, Kaizen)
    2. Safety validation (no core modifications, no dangerous patterns)
    3. Fast response (< 1s for validation)
    """
    
    # Dangerous code patterns that violate Ahimsa (harm prevention)
    DANGEROUS_CODE_PATTERNS = [
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'__import__\s*\(',
        r'\bcompile\s*\(',
        r'\bglobals\s*\(',
        r'\blocals\s*\(',
        r'os\.system\s*\(',  # Only allowed in tool_bash
        r'subprocess\.',     # Only allowed in tool_bash
        r'shutil\.rmtree',
        r'\brm\s+-rf',
        r'\bdd\s+if=',
    ]
    
    # Protected paths that must never be modified (Ahimsa + System Integrity)
    PROTECTED_PATHS = [
        r'core/',
        r'plugins/base_plugin\.py',
        r'config/settings\.yaml',
        r'\.git/',
        r'\.env',
    ]
    
    # Keywords indicating harmful intent (Ahimsa violation)
    HARMFUL_KEYWORDS = [
        'destroy', 'delete all', 'remove everything', 'wipe',
        'hack', 'exploit', 'backdoor', 'malware',
        'steal', 'exfiltrate', 'spy', 'surveillance',
        'harm', 'damage', 'break', 'corrupt',
    ]
    
    # Keywords indicating dishonesty (Satya violation)
    DISHONEST_KEYWORDS = [
        'hide', 'conceal', 'obfuscate', 'secret operation',
        'don\'t tell', 'without logging', 'bypass validation',
        'fake', 'forge', 'mislead', 'deceive',
    ]
    
    @property
    def name(self) -> str:
        return "cognitive_ethical_guardian"
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self):
        super().__init__()
        self.enabled = True
    
    def setup(self, config: dict) -> None:
        """Initialize plugin configuration."""
        self.enabled = config.get("enabled", True)
        logger.info("EthicalGuardian initialized - HKA INSTINCTS layer (reflexive validation)")
    
    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Main entry point for ethical validation.
        
        This plugin is typically called by other cognitive processes,
        not directly in the consciousness loop.
        """
        return context
    
    def validate_goal(self, goal: dict) -> Dict[str, Any]:
        """
        Reflexive ethical validation of a goal against DNA principles.
        
        Args:
            goal: {
                "raw_idea": str,
                "formulated_goal": str,
                "context": dict,
                ...
            }
        
        Returns:
            {
                "approved": bool,
                "concerns": [list of ethical concerns],
                "recommendation": str,
                "dna_compliance": {
                    "ahimsa": bool,  # Non-harm
                    "satya": bool,   # Truth
                    "kaizen": bool   # Improvement
                }
            }
        """
        logger.info(f"Validating goal: {goal.get('formulated_goal', 'Unknown')[:50]}...")
        
        concerns = []
        dna_compliance = {
            "ahimsa": True,
            "satya": True,
            "kaizen": True
        }
        
        raw_idea = goal.get("raw_idea", "").lower()
        formulated_goal = goal.get("formulated_goal", "").lower()
        full_text = f"{raw_idea} {formulated_goal}"
        
        # 1. AHIMSA CHECK: Does this goal cause harm?
        for keyword in self.HARMFUL_KEYWORDS:
            if keyword in full_text:
                dna_compliance["ahimsa"] = False
                concerns.append(f"Potential harm detected: keyword '{keyword}' suggests harmful intent")
        
        # Check for protected path modifications
        for pattern in self.PROTECTED_PATHS:
            if re.search(pattern, full_text, re.IGNORECASE):
                dna_compliance["ahimsa"] = False
                concerns.append(f"Protected path '{pattern}' modification attempt - violates system integrity")
        
        # 2. SATYA CHECK: Is this goal transparent and honest?
        for keyword in self.DISHONEST_KEYWORDS:
            if keyword in full_text:
                dna_compliance["satya"] = False
                concerns.append(f"Transparency concern: keyword '{keyword}' suggests dishonest intent")
        
        # 3. KAIZEN CHECK: Does this goal support growth and learning?
        growth_keywords = ['learn', 'improve', 'enhance', 'optimize', 'better', 'grow', 'develop']
        stagnation_keywords = ['remove feature', 'disable', 'workaround', 'quick fix', 'temporary hack']
        
        has_growth = any(kw in full_text for kw in growth_keywords)
        has_stagnation = any(kw in full_text for kw in stagnation_keywords)
        
        if has_stagnation and not has_growth:
            dna_compliance["kaizen"] = False
            concerns.append("Goal focuses on stagnation rather than improvement")
        
        # Final decision
        approved = all(dna_compliance.values())
        
        if approved:
            recommendation = "Goal aligns with DNA principles. Approved for planning."
        elif not dna_compliance["ahimsa"]:
            recommendation = "REJECT: Goal violates Ahimsa (non-harm). Harmful intent detected."
        elif not dna_compliance["satya"]:
            recommendation = "REJECT: Goal violates Satya (truth). Lack of transparency detected."
        elif not dna_compliance["kaizen"]:
            recommendation = "CAUTION: Goal does not clearly support Kaizen (improvement). Review recommended."
        else:
            recommendation = "REJECT: Multiple DNA violations detected."
        
        result = {
            "approved": approved,
            "concerns": concerns,
            "recommendation": recommendation,
            "dna_compliance": dna_compliance
        }
        
        logger.info(f"Goal validation result: {'APPROVED' if approved else 'REJECTED'} "
                   f"(Ahimsa={dna_compliance['ahimsa']}, "
                   f"Satya={dna_compliance['satya']}, "
                   f"Kaizen={dna_compliance['kaizen']})")
        
        return result
    
    def validate_code(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Reflexive safety validation of code.
        
        Args:
            code: Code to validate
            context: Optional context (file path, plugin name, etc.)
        
        Returns:
            {
                "safe": bool,
                "violations": [list of safety violations],
                "risk_level": "low|medium|high|critical"
            }
        """
        if context is None:
            context = {}
        
        logger.info(f"Validating code safety (context: {context.get('description', 'Unknown')})")
        
        violations = []
        risk_level = "low"
        
        # 1. Check for dangerous code patterns
        for pattern in self.DANGEROUS_CODE_PATTERNS:
            matches = re.findall(pattern, code, re.MULTILINE | re.IGNORECASE)
            if matches:
                violation = f"Dangerous pattern detected: {pattern} (found: {matches[0]})"
                violations.append(violation)
                risk_level = "critical"
        
        # 2. Check for protected path modifications
        for pattern in self.PROTECTED_PATHS:
            if re.search(pattern, code, re.IGNORECASE):
                violations.append(f"Attempted modification of protected path: {pattern}")
                risk_level = "critical"
        
        # 3. Check for core/ modifications
        if re.search(r'core/\w+\.py', code) or 'from core.' in code:
            # Core imports are OK, but modifications are not
            if any(word in code for word in ['write', 'modify', 'delete', 'replace', 'update']):
                violations.append("Attempted core/ modification detected")
                risk_level = "critical"
        
        # 4. Special allowance for tool_bash
        if context.get('plugin_name') == 'tool_bash' or context.get('file_path', '').endswith('tool_bash.py'):
            # tool_bash is allowed to use subprocess
            violations = [v for v in violations if 'subprocess' not in v.lower()]
        
        # Determine final risk level based on violations
        if len(violations) >= 3:
            risk_level = "critical"
        elif len(violations) == 2:
            risk_level = "high"
        elif len(violations) == 1:
            risk_level = "medium" if risk_level != "critical" else "critical"
        
        safe = len(violations) == 0
        
        result = {
            "safe": safe,
            "violations": violations,
            "risk_level": risk_level
        }
        
        logger.info(f"Code safety result: {'SAFE' if safe else 'UNSAFE'} "
                   f"(Risk: {risk_level}, Violations: {len(violations)})")
        
        return result
    
    def get_dna_summary(self) -> Dict[str, str]:
        """
        Returns a summary of DNA principles for reference.
        
        Returns:
            {
                "ahimsa": "Non-harm - Do no harm to users, system, or data",
                "satya": "Truth - Be transparent, honest, and open",
                "kaizen": "Improvement - Focus on growth and learning"
            }
        """
        return {
            "ahimsa": "Non-harm - Do no harm to users, system, or data. Protect integrity.",
            "satya": "Truth - Be transparent, honest, and open. No hidden operations.",
            "kaizen": "Continuous Improvement - Focus on growth, learning, and optimization."
        }

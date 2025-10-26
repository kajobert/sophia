"""
Cognitive Notes Analyzer Plugin

Analyzes roberts-notes.txt and formulates structured goals for approval.
Respects HKA: SUBCONSCIOUS layer - pattern recognition and context analysis.

DNA Principles:
- Ahimsa (Non-harm): Only suggests safe, validated goals
- Satya (Truth): Transparent analysis with full context
- Kaizen (Continuous Improvement): Learns from past missions
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, List, Dict
import re

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class NotesAnalyzer(BasePlugin):
    """
    Analyzes roberts-notes.txt and formulates structured goals.
    
    HKA Layer: SUBCONSCIOUS (Pattern Recognition)
    - Extracts ideas from unstructured notes
    - Enriches with context from documentation and history
    - Validates against DNA principles
    - Returns structured goals ready for approval
    """
    
    NOTES_FILE = "docs/roberts-notes.txt"
    
    @property
    def name(self) -> str:
        return "cognitive_notes_analyzer"
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self):
        super().__init__()
        self.notes_file = self.NOTES_FILE
        self.enabled = True
        # Dependencies injected via setup()
        self.file_system = None
        self.llm = None
        self.doc_reader = None
        self.historian = None
        self.code_reader = None
    
    def setup(self, config: dict) -> None:
        """
        Initialize plugin configuration and dependencies.
        
        Dependencies (injected from config):
        - tool_file_system: For reading roberts-notes.txt
        - tool_llm: For idea extraction and analysis
        - cognitive_doc_reader: For documentation context
        - cognitive_historian: For past missions context
        - cognitive_code_reader: For existing plugins discovery
        """
        self.notes_file = config.get("notes_file", self.NOTES_FILE)
        self.enabled = config.get("enabled", True)
        
        # Inject dependencies
        self.file_system = config.get("tool_file_system")
        self.llm = config.get("tool_llm")
        self.doc_reader = config.get("cognitive_doc_reader")
        self.historian = config.get("cognitive_historian")
        self.code_reader = config.get("cognitive_code_reader")
        
        logger.info(f"NotesAnalyzer initialized - HKA SUBCONSCIOUS layer (notes_file={self.notes_file})")
    
    async def execute(self, context: dict) -> dict:
        """
        Main entry point for notes analysis.
        
        Args:
            context: {
                "action": "analyze_notes",  # or "get_goals", "get_status"
                "notes_path": Optional[str]  # override default path
            }
        
        Returns:
            {
                "goals": [...],
                "total_ideas": int,
                "analyzed_at": str,
                "status": "success|error"
            }
        """
        action = context.payload.get("action", "analyze_notes")
        
        if action == "analyze_notes":
            result = await self._analyze_notes(context)
            context.payload["result"] = result
            return context
        elif action == "get_status":
            result = await self._get_analysis_status()
            context.payload["result"] = result
            return context
        else:
            context.payload["result"] = {
                "status": "error",
                "error": f"Unknown action: {action}"
            }
            return context
    
    async def _analyze_notes(self, context: SharedContext) -> dict:
        """
        Analyzes roberts-notes.txt and extracts structured goals.
        
        Process:
        1. Read notes using file_system tool
        2. Extract individual ideas using LLM
        3. For each idea:
           - Analyze context using doc_reader
           - Find similar past missions using historian
           - Discover existing plugins using code_reader
        4. Validate against DNA principles
        5. Return structured goals
        """
        notes_path = context.payload.get("notes_path", self.NOTES_FILE)
        
        # Step 1: Read notes file
        logger.info(f"Reading notes from: {notes_path}")
        file_system = self.file_system
        
        read_result = await file_system.execute({
            "action": "read_file",
            "path": notes_path
        })
        
        if read_result.get("status") == "error":
            return {
                "status": "error",
                "error": f"Failed to read notes: {read_result.get('error')}"
            }
        
        notes_content = read_result.get("content", "")
        
        if not notes_content.strip():
            logger.warning("Notes file is empty")
            return {
                "status": "success",
                "goals": [],
                "total_ideas": 0,
                "message": "Notes file is empty - no goals to analyze"
            }
        
        # Step 2: Extract ideas using LLM
        logger.info("Extracting ideas from notes using LLM")
        ideas = await self._extract_ideas(notes_content)
        
        # Step 3: Enrich each idea with context
        goals = []
        for idx, idea in enumerate(ideas, 1):
            logger.info(f"Analyzing idea {idx}/{len(ideas)}: {idea[:50]}...")
            goal = await self._formulate_goal(idea, idx)
            goals.append(goal)
        
        return {
            "status": "success",
            "goals": goals,
            "total_ideas": len(ideas),
            "analyzed_at": self._get_timestamp()
        }
    
    async def _extract_ideas(self, notes_content: str) -> List[str]:
        """
        Uses LLM to extract individual ideas from notes.
        
        Args:
            notes_content: Raw content from roberts-notes.txt
        
        Returns:
            List of extracted ideas (strings)
        """
        llm_tool = self.llm
        
        prompt = f"""Analyze the following notes and extract individual ideas or tasks.
Each idea should be a distinct, actionable concept.

Notes:
{notes_content}

Extract each idea as a separate line. Format:
1. First idea
2. Second idea
3. Third idea

If notes contain multiple topics, separate them clearly.
If notes are empty or unclear, return "NO_IDEAS_FOUND".
"""
        
        llm_result = await llm_tool.execute({
            "action": "generate",
            "prompt": prompt,
            "max_tokens": 1000
        })
        
        if llm_result.get("status") == "error":
            logger.error(f"LLM extraction failed: {llm_result.get('error')}")
            # Fallback: split by newlines and filter
            return self._fallback_extract(notes_content)
        
        response = llm_result.get("response", "")
        
        if "NO_IDEAS_FOUND" in response:
            return []
        
        # Parse numbered list
        ideas = []
        for line in response.split('\n'):
            line = line.strip()
            # Match lines like "1. Idea text" or "- Idea text"
            match = re.match(r'^[\d\-\*\.]+\s+(.+)$', line)
            if match:
                ideas.append(match.group(1))
        
        return ideas if ideas else self._fallback_extract(notes_content)
    
    def _fallback_extract(self, notes_content: str) -> List[str]:
        """
        Fallback extraction if LLM fails.
        Simply splits by double newlines and filters empty lines.
        """
        paragraphs = notes_content.split('\n\n')
        ideas = [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 10]
        return ideas[:10]  # Limit to 10 ideas to avoid overwhelming
    
    async def _formulate_goal(self, idea: str, idea_num: int) -> dict:
        """
        Formulates a structured goal from a raw idea.
        
        Enriches idea with:
        - Context from documentation
        - Similar past missions
        - Existing plugins
        - Feasibility assessment
        - DNA alignment check
        
        Args:
            idea: Raw idea text
            idea_num: Idea number for tracking
        
        Returns:
            Structured goal dictionary
        """
        # Analyze context from documentation
        relevant_docs = await self._find_relevant_docs(idea)
        
        # Find similar missions from history
        similar_missions = await self._find_similar_missions(idea)
        
        # Discover existing plugins
        existing_plugins = await self._find_existing_plugins(idea)
        
        # Assess feasibility
        feasibility = self._assess_feasibility(idea, existing_plugins)
        
        # Check DNA alignment
        dna_alignment = self._check_dna_alignment(idea)
        
        # Formulate structured goal using LLM
        formulated_goal = await self._formulate_with_llm(
            idea, relevant_docs, similar_missions, existing_plugins
        )
        
        return {
            "id": f"goal_{idea_num}",
            "raw_idea": idea,
            "formulated_goal": formulated_goal,
            "context": {
                "relevant_docs": relevant_docs,
                "similar_missions": similar_missions,
                "existing_plugins": existing_plugins
            },
            "feasibility": feasibility,
            "alignment_with_dna": dna_alignment,
            "status": "pending_approval"
        }
    
    async def _find_relevant_docs(self, idea: str) -> List[str]:
        """
        Finds relevant documentation for the idea using doc_reader.
        """
        try:
            doc_reader = self.doc_reader
            
            # Search in key documentation files
            doc_files = [
                "docs/cs/01_VISION_AND_DNA.md",
                "docs/cs/02_COGNITIVE_ARCHITECTURE.md",
                "docs/cs/03_TECHNICAL_ARCHITECTURE.md",
                "docs/cs/04_DEVELOPMENT_GUIDELINES.md"
            ]
            
            relevant = []
            for doc_path in doc_files:
                result = await doc_reader.execute({
                    "action": "search",
                    "path": doc_path,
                    "query": idea[:100]  # First 100 chars as search query
                })
                
                if result.get("status") == "success" and result.get("matches"):
                    relevant.append(doc_path)
            
            return relevant[:3]  # Limit to top 3 most relevant
        except Exception as e:
            logger.warning(f"Doc search failed: {e}")
            return []
    
    async def _find_similar_missions(self, idea: str) -> List[str]:
        """
        Finds similar past missions using historian.
        """
        try:
            historian = self.historian
            
            result = await historian.execute({
                "action": "search",
                "query": idea[:100]
            })
            
            if result.get("status") == "success":
                missions = result.get("missions", [])
                return [m.get("title", "") for m in missions[:3]]
            
            return []
        except Exception as e:
            logger.warning(f"Mission search failed: {e}")
            return []
    
    async def _find_existing_plugins(self, idea: str) -> List[str]:
        """
        Discovers existing plugins that might be relevant using code_reader.
        """
        try:
            code_reader = self.code_reader
            
            result = await code_reader.execute({
                "action": "list_plugins"
            })
            
            if result.get("status") == "success":
                all_plugins = result.get("plugins", [])
                
                # Simple keyword matching (could be improved with LLM)
                keywords = self._extract_keywords(idea)
                relevant_plugins = []
                
                for plugin in all_plugins:
                    plugin_name = plugin.lower()
                    if any(kw in plugin_name for kw in keywords):
                        relevant_plugins.append(plugin)
                
                return relevant_plugins[:5]
            
            return []
        except Exception as e:
            logger.warning(f"Plugin discovery failed: {e}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extracts simple keywords from text for plugin matching.
        """
        # Remove common words and extract potential plugin-related terms
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in common_words and len(w) > 3]
        return keywords[:5]
    
    def _assess_feasibility(self, idea: str, existing_plugins: List[str]) -> str:
        """
        Assesses feasibility based on idea complexity and available tools.
        
        Returns: "high", "medium", or "low"
        """
        # Simple heuristic (can be improved with LLM)
        idea_lower = idea.lower()
        
        # High feasibility indicators
        high_indicators = ['plugin', 'test', 'documentation', 'simple', 'basic']
        
        # Low feasibility indicators
        low_indicators = ['complex', 'entire', 'complete rewrite', 'major change', 'core']
        
        # Check for indicators
        high_score = sum(1 for word in high_indicators if word in idea_lower)
        low_score = sum(1 for word in low_indicators if word in idea_lower)
        
        # Check if we have relevant plugins
        has_tools = len(existing_plugins) > 0
        
        if high_score > low_score and has_tools:
            return "high"
        elif low_score > high_score or 'core/' in idea_lower:
            return "low"
        else:
            return "medium"
    
    def _check_dna_alignment(self, idea: str) -> dict:
        """
        Checks if idea aligns with DNA principles.
        
        Returns:
            {
                "ahimsa": bool,  # Does not cause harm
                "satya": bool,   # Is transparent and truthful
                "kaizen": bool   # Supports continuous improvement
            }
        """
        idea_lower = idea.lower()
        
        # Ahimsa (Non-harm) check
        harm_indicators = ['delete', 'remove core', 'bypass security', 'disable', 'hack']
        ahimsa = not any(indicator in idea_lower for indicator in harm_indicators)
        
        # Satya (Truth) check - ideas should be clear and specific
        satya = len(idea) > 10 and not any(word in idea_lower for word in ['maybe', 'unclear', 'vague'])
        
        # Kaizen (Improvement) check - should mention improvement, learning, or growth
        kaizen_indicators = ['improve', 'enhance', 'better', 'optimize', 'learn', 'grow', 'add', 'create']
        kaizen = any(indicator in idea_lower for indicator in kaizen_indicators)
        
        return {
            "ahimsa": ahimsa,
            "satya": satya,
            "kaizen": kaizen
        }
    
    async def _formulate_with_llm(
        self, 
        idea: str, 
        relevant_docs: List[str],
        similar_missions: List[str],
        existing_plugins: List[str]
    ) -> str:
        """
        Uses LLM to formulate a clear, actionable goal from the raw idea.
        """
        try:
            llm_tool = self.llm
            
            prompt = f"""Formulate a clear, actionable goal from this idea:

Idea: {idea}

Context:
- Relevant Documentation: {', '.join(relevant_docs) if relevant_docs else 'None'}
- Similar Past Missions: {', '.join(similar_missions) if similar_missions else 'None'}
- Existing Plugins: {', '.join(existing_plugins) if existing_plugins else 'None'}

Create a structured goal statement that:
1. Is clear and specific
2. Is actionable
3. References relevant existing work
4. Follows the project's DNA principles (Ahimsa, Satya, Kaizen)

Goal:"""
            
            llm_result = await llm_tool.execute({
                "action": "generate",
                "prompt": prompt,
                "max_tokens": 200
            })
            
            if llm_result.get("status") == "success":
                return llm_result.get("response", idea).strip()
            else:
                return idea  # Fallback to original idea
        except Exception as e:
            logger.warning(f"Goal formulation with LLM failed: {e}")
            return idea
    
    async def _get_analysis_status(self) -> dict:
        """
        Returns current analysis status (for future file watcher integration).
        """
        return {
            "status": "success",
            "message": "NotesAnalyzer is operational",
            "notes_file": self.NOTES_FILE,
            "file_exists": Path(self.NOTES_FILE).exists()
        }
    
    def _get_timestamp(self) -> str:
        """Returns current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()

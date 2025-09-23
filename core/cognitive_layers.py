import logging
from core.llm_config import LLMConfig


# A mock for the nano model call
def call_nano_model_mock(prompt: str) -> str:
    """A mock function to simulate a call to a local, fast LLM."""
    if "strukturuj" in prompt.lower():
        return '{"action": "categorize", "priority": "high"}'
    return '{"action": "unknown", "priority": "low"}'


class ReptilianBrain:
    """
    The most primitive layer of the cognitive architecture.
    It is responsible for instinctual, immediate reactions, and basic safety checks.
    It operates based on a hardcoded "DNA".
    """

    def __init__(self, llm_config: LLMConfig, dna_path: str = "docs/DNA.md"):
        self.logger = logging.getLogger(__name__)
        self.dna = self._load_dna(dna_path)
        # In a real scenario, this would be a proper LLM client (e.g., Ollama)
        self.nano_model = call_nano_model_mock
        self.logger.info("ReptilianBrain initialized.")

    def _load_dna(self, dna_path: str) -> str:
        """
        Loads the agent's core directives from a Markdown file.
        Uses the 'marko' library for robust parsing.
        """
        try:
            with open(dna_path, "r", encoding="utf-8") as f:
                markdown_content = f.read()
                # Marko can be used to parse and process the markdown,
                # but for now, we'll just return the raw text.
                return markdown_content
        except FileNotFoundError:
            self.logger.error(
                f"DNA file not found at {dna_path}. The agent will operate without its core directives."
            )
            return "Error: DNA not loaded."

    def _call_nano_model(self, prompt: str) -> str:
        """
        Calls a very fast, local "nano" model for quick tasks like categorization or structuring.
        """
        self.logger.info(f"Calling nano model with prompt: {prompt[:100]}...")
        # This is a placeholder for a real local LLM call (e.g., via Ollama)
        return self.nano_model(prompt)

    def process_input(self, user_input: str) -> dict:
        """
        Processes the user input through the reptilian layer.
        Performs a basic safety check based on the DNA and uses the nano model
        to add initial structure.
        """
        self.logger.info("ReptilianBrain processing input.")

        # Basic safety check (placeholder)
        if "rm -rf" in user_input:
            raise ValueError(
                "Input contains a potentially dangerous command and was blocked by the ReptilianBrain."
            )

        # Use the nano model to get initial structure
        structuring_prompt = f"Strukturuj nasledujici pozadavek: {user_input}"
        structured_data_str = self._call_nano_model(structuring_prompt)

        try:
            structured_data = eval(
                structured_data_str
            )  # Using eval for mock, in real use json.loads
        except Exception:
            structured_data = {"action": "parsing_failed", "priority": "medium"}

        processed_data = {
            "original_input": user_input,
            "structured_input": structured_data,
            "dna_directives": self.dna,
            "safety_passed": True,
        }
        return processed_data


class MammalianBrain:
    """
    The second layer, responsible for emotions, social context, and memory retrieval.
    It enriches the input with emotional context and relevant past experiences.
    """

    def __init__(self, long_term_memory):
        self.logger = logging.getLogger(__name__)
        self.ltm = long_term_memory
        self.logger.info("MammalianBrain initialized.")

    def process_input(self, processed_data: dict) -> dict:
        """
        Enriches the processed data with context from long-term memory.
        """
        self.logger.info("MammalianBrain processing input.")
        query = processed_data.get("original_input", "")

        # Search for relevant memories
        relevant_memories = self.ltm.search_knowledge(query, top_k=3)

        # Add memories to the data payload
        processed_data["relevant_memories"] = relevant_memories

        # Placeholder for emotional analysis
        processed_data["emotional_context"] = "neutral"

        return processed_data

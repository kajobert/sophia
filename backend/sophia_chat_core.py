import asyncio
import logging
import traceback
import os
from backend.database_manager import DatabaseManager
from core.llm_manager import LLMManager

logger = logging.getLogger(__name__)

class SophiaChatCore:
    def __init__(self, prompts_dir="prompts/sophia"):
        logger.info("Initializing SophiaChatCore...")
        self.db_manager = DatabaseManager()
        self.llm_manager = LLMManager()

        # Load persona and system prompt from external files
        try:
            with open(os.path.join(prompts_dir, "sophia_dna.txt"), "r", encoding="utf-8") as f:
                self.sophia_dna = f.read()
            with open(os.path.join(prompts_dir, "sophia_system_prompt.txt"), "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
            logger.info("Successfully loaded Sophia's DNA and system prompt.")
        except FileNotFoundError:
            logger.error(f"FATAL: Prompt files not found in '{prompts_dir}'. Make sure 'sophia_dna.txt' and 'sophia_system_prompt.txt' exist.")
            # In a real application, you might want to fall back to a default or raise an exception.
            # For this MVP, we will proceed but expect errors.
            self.sophia_dna = "You are a helpful assistant."
            self.system_prompt = "Please answer the user's question."

    async def handle_message(self, session_id: str, user_message: str):
        """
        Handles an incoming user message with a robust, multi-layered prompt.
        """
        logger.info(f"[{session_id}] Handling new message...")
        response_text = ""
        try:
            self.db_manager.add_message(session_id, 'user', user_message)
            self.db_manager.add_memory(session_id, user_message, metadata={'role': 'user'})

            relevant_memories = self.db_manager.query_memory(session_id, user_message, n_results=5)
            recent_messages_tuples = self.db_manager.get_recent_messages(session_id, limit=15)
            recent_messages = [{"role": msg[2], "content": msg[3]} for msg in recent_messages_tuples]

            prompt = self._build_prompt(relevant_memories, recent_messages)

            logger.debug(f"[{session_id}] Sending final prompt to LLM:\n--- PROMPT START ---\n{prompt}\n--- PROMPT END ---")

            llm_adapter = self.llm_manager.get_llm("powerful")

            if not llm_adapter:
                raise ValueError("LLMManager failed to provide a valid adapter.")

            llm_response, _ = await llm_adapter.generate_content_async(prompt)

            if isinstance(llm_response, str) and llm_response:
                response_text = llm_response
            else:
                logger.error(f"[{session_id}] Adapter returned an invalid response. Type: {type(llm_response)}, Content: {llm_response}")
                response_text = "I apologize, but I received an empty or invalid response from my core intelligence. Please try again."

        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"[{session_id}] An exception occurred in handle_message:\n{error_traceback}")
            response_text = f"An internal error occurred. Please send this to the developer:\n\n{error_traceback}"

        self.db_manager.add_message(session_id, 'assistant', response_text)
        self.db_manager.add_memory(session_id, response_text, metadata={'role': 'assistant'})

        logger.info(f"[{session_id}] Sending final response to frontend.")
        return response_text

    def _build_prompt(self, memories, history):
        """
        Builds a high-quality, robust prompt from the loaded DNA, system prompt, and conversation context.
        """
        prompt_parts = [
            "**## YOUR CORE IDENTITY (DNA) ##**",
            self.sophia_dna,
            "\n**## YOUR INSTRUCTIONS (SYSTEM PROMPT) ##**",
            self.system_prompt
        ]

        if memories:
            prompt_parts.append("\n**## RELEVANT MEMORIES (for long-term context) ##**")
            for mem in memories:
                prompt_parts.append(f"- {mem}")

        if history:
            prompt_parts.append("\n**## CURRENT CONVERSATION HISTORY ##**")
            for msg in history:
                role = "User" if msg['role'] == 'user' else "Sophia"
                prompt_parts.append(f"{role}: {msg['content']}")

        # The final instruction for the AI.
        prompt_parts.append("\n**## YOUR TASK ##**")
        prompt_parts.append("Based on all the information above, provide your response as Sophia.")

        return "\n\n".join(prompt_parts)

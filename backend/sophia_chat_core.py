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

        try:
            with open(os.path.join(prompts_dir, "sophia_dna.txt"), "r", encoding="utf-8") as f:
                self.sophia_dna = f.read()
            with open(os.path.join(prompts_dir, "sophia_system_prompt.txt"), "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
            logger.info("Successfully loaded Sophia's DNA and system prompt.")
        except FileNotFoundError:
            logger.error(f"FATAL: Prompt files not found in '{prompts_dir}'.")
            self.sophia_dna = "You are a helpful assistant."
            self.system_prompt = "Please answer the user's question."

    async def handle_message(self, session_id: str, user_message: str):
        logger.info(f"[{session_id}] Handling new message...")
        response_text = ""
        try:
            self.db_manager.add_message(session_id, 'user', user_message)
            self.db_manager.add_memory(session_id, user_message, metadata={'role': 'user'})

            relevant_memories = self.db_manager.query_memory(session_id, user_message, n_results=5)
            recent_messages_tuples = self.db_manager.get_recent_messages(session_id, limit=15)

            # This now includes the latest user message
            conversation_history = [{"role": msg[2], "content": msg[3]} for msg in recent_messages_tuples]

            # **THE FIX: Build a structured list of messages, not a single string prompt.**
            messages = self._build_messages(relevant_memories, conversation_history)

            logger.debug(f"[{session_id}] Sending final messages structure to LLM:\n{messages}")

            llm_adapter = self.llm_manager.get_llm("powerful")

            if not llm_adapter:
                raise ValueError("LLMManager failed to provide a valid adapter.")

            # The adapter will now receive the structured list of messages.
            llm_response, _ = await llm_adapter.generate_content_async(messages)

            if isinstance(llm_response, str) and llm_response:
                response_text = llm_response
            else:
                logger.error(f"[{session_id}] Adapter returned an invalid response. Type: {type(llm_response)}, Content: {llm_response}")
                response_text = "I apologize, but I received an empty or invalid response from my core intelligence."

        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"[{session_id}] An exception occurred in handle_message:\n{error_traceback}")
            response_text = f"An internal error occurred. Traceback:\n\n{error_traceback}"

        self.db_manager.add_message(session_id, 'assistant', response_text)
        self.db_manager.add_memory(session_id, response_text, metadata={'role': 'assistant'})

        logger.info(f"[{session_id}] Sending final response to frontend.")
        return response_text

    def _build_messages(self, memories, history) -> list[dict]:
        """
        Builds a structured list of messages for the LLM, respecting roles.
        """
        # Combine DNA and system prompt into a single, powerful system message.
        system_content = f"{self.sophia_dna}\n\n{self.system_prompt}"

        # Add memories to the system content for context.
        if memories:
            memory_str = "\n\n**Relevant Memories for Context:**\n" + "\n".join(f"- {mem}" for mem in memories)
            system_content += memory_str

        messages = [{"role": "system", "content": system_content}]

        # Add the conversation history, ensuring correct roles.
        for msg in history:
            # The role is already 'user' or 'assistant', which is the correct format.
            messages.append({"role": msg["role"], "content": msg["content"]})

        return messages

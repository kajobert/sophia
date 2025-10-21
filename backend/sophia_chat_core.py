import asyncio
import logging
import traceback # Import traceback module
from backend.database_manager import DatabaseManager
from core.llm_manager import LLMManager

logger = logging.getLogger(__name__)

class SophiaChatCore:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.llm_manager = LLMManager()

    async def handle_message(self, session_id: str, user_message: str):
        """
        Handles an incoming user message, generates a response, and stores the conversation.
        """
        response_text = ""
        try:
            # 1. Store the user's message
            self.db_manager.add_message(session_id, 'user', user_message)
            self.db_manager.add_memory(session_id, user_message, metadata={'role': 'user'})

            # 2. Retrieve context
            relevant_memories = self.db_manager.query_memory(session_id, user_message)
            recent_messages_tuples = self.db_manager.get_recent_messages(session_id)

            recent_messages = [
                {"role": msg[2], "content": msg[3]} for msg in recent_messages_tuples
            ]

            # 3. Construct the prompt
            prompt = self._build_prompt(relevant_memories, recent_messages, user_message)

            # 4. Get AI response
            llm_adapter = self.llm_manager.get_llm("powerful")
            response_text, _ = await llm_adapter.generate_content_async(prompt)

        except Exception as e:
            # **DEBUGGING WITH BRUTE FORCE:**
            # Capture the full traceback and send it to the frontend.
            error_traceback = traceback.format_exc()
            logger.error(f"Caught exception for session {session_id}:\n{error_traceback}")
            response_text = f"An error occurred inside the container. Please send this to the developer:\n\n{error_traceback}"

        # 5. Store AI response (even if it's an error message)
        # This helps in logging and understanding the flow.
        self.db_manager.add_message(session_id, 'assistant', response_text)
        self.db_manager.add_memory(session_id, response_text, metadata={'role': 'assistant'})

        # 6. Return the response
        return response_text

    def _build_prompt(self, memories, history, new_message):
        """Builds the final prompt string for the LLM."""
        prompt_parts = []

        prompt_parts.append("### System Prompt")
        prompt_parts.append("You are Sophia, a helpful AI assistant.")
        prompt_parts.append("\n### Relevant Memories (from past conversations)")
        if memories:
            for mem in memories:
                prompt_parts.append(f"- {mem}")
        else:
            prompt_parts.append("No relevant memories found.")

        prompt_parts.append("\n### Recent Conversation History")
        if history:
            for msg in history:
                prompt_parts.append(f"{msg['role'].title()}: {msg['content']}")
        else:
            prompt_parts.append("No recent history.")

        prompt_parts.append("\n### New User Message")
        prompt_parts.append(f"User: {new_message}")

        prompt_parts.append("\n### Your Response")
        prompt_parts.append("Assistant:")

        return "\n".join(prompt_parts)

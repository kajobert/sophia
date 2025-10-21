import asyncio
import logging
import traceback
from backend.database_manager import DatabaseManager
from core.llm_manager import LLMManager

# Use the logger configured in run.py
logger = logging.getLogger(__name__)

class SophiaChatCore:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.llm_manager = LLMManager()
        logger.info("SophiaChatCore instance has been initialized.")

    async def handle_message(self, session_id: str, user_message: str):
        """
        Handles an incoming user message with extensive diagnostic logging.
        """
        logger.info(f"[{session_id}] Received a new message.")
        response_text = ""
        try:
            # 1. Store the user's message
            logger.info(f"[{session_id}] Storing user message to DB...")
            self.db_manager.add_message(session_id, 'user', user_message)
            self.db_manager.add_memory(session_id, user_message, metadata={'role': 'user'})
            logger.info(f"[{session_id}] User message stored.")

            # 2. Retrieve context
            logger.info(f"[{session_id}] Querying for relevant memories and recent messages...")
            relevant_memories = self.db_manager.query_memory(session_id, user_message)
            recent_messages_tuples = self.db_manager.get_recent_messages(session_id)
            logger.info(f"[{session_id}] Found {len(relevant_memories)} memories and {len(recent_messages_tuples)} recent messages.")

            # 3. Construct the prompt
            prompt = self._build_prompt(relevant_memories, recent_messages_tuples, user_message)
            logger.info(f"[{session_id}] Prompt constructed for LLM.")

            # 4. Get AI response
            logger.info(f"[{session_id}] Requesting LLM adapter for alias 'powerful'...")
            llm_adapter = self.llm_manager.get_llm("powerful")

            # **Diagnostic Log (for Scenario 2):** Check if the adapter is valid.
            if llm_adapter:
                logger.info(f"[{session_id}] Adapter received: {type(llm_adapter).__name__}")
            else:
                logger.error(f"[{session_id}] FATAL: LLMManager returned a None adapter.")
                raise ValueError("LLMManager failed to provide a valid adapter.")

            logger.info(f"[{session_id}] Calling generate_content_async on the adapter...")
            llm_response, _ = await llm_adapter.generate_content_async(prompt)
            logger.info(f"[{session_id}] Received response from adapter. Type: {type(llm_response)}")

            # Defensive Check
            if isinstance(llm_response, str):
                response_text = llm_response
                logger.info(f"[{session_id}] Response is a string. Processing as final answer.")
            else:
                logger.error(f"[{session_id}] Unexpected response type from adapter: {type(llm_response)}. Full response: {llm_response}")
                response_text = "I received an unexpected response format from the AI."

        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"[{session_id}] An exception occurred:\n{error_traceback}")
            response_text = f"An error occurred. Traceback:\n\n{error_traceback}"

        # 5. Store AI response
        logger.info(f"[{session_id}] Storing final response to DB: '{response_text[:100]}...'")
        self.db_manager.add_message(session_id, 'assistant', response_text)
        self.db_manager.add_memory(session_id, response_text, metadata={'role': 'assistant'})

        # 6. Return the response
        logger.info(f"[{session_id}] Sending response to frontend.")
        return response_text

    def _build_prompt(self, memories, history, new_message):
        """Builds the final prompt string for the LLM."""
        prompt_parts = []
        prompt_parts.append("### System Prompt...") # (rest of the prompt is omitted for brevity)
        return "\n".join(prompt_parts)

import asyncio
import logging
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
        try:
            llm_adapter = self.llm_manager.get_llm("powerful")
            # The method returns a tuple: (response_object, usage_data)
            assistant_response_obj, _ = await llm_adapter.generate_content_async(prompt)

            # **THE FIX:** Correctly extract the text content from the response object.
            response_text = assistant_response_obj.choices[0].message.content

        except Exception as e:
            logger.error(f"Error processing LLM response for session {session_id}", exc_info=True)
            response_text = "I'm sorry, I encountered an error while processing your request."

        # 5. Store AI response
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

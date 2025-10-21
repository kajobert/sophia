import asyncio
from backend.database_manager import DatabaseManager
from core.llm_manager import LLMManager

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

        # 2. Retrieve context (memories and recent messages)
        relevant_memories = self.db_manager.query_memory(session_id, user_message)
        recent_messages_tuples = self.db_manager.get_recent_messages(session_id)

        # Convert tuples to a more usable format
        recent_messages = [
            {"role": msg[2], "content": msg[3]} for msg in recent_messages_tuples
        ]

        # 3. Construct the prompt
        prompt = self._build_prompt(relevant_memories, recent_messages, user_message)

        # 4. Get AI response
        # **CORRECTED LOGIC AGAIN:** Use the correct method name `generate_content_async`.
        try:
            llm_adapter = self.llm_manager.get_llm("powerful")
            # The method returns a tuple: (content, usage_data)
            assistant_response, _ = await llm_adapter.generate_content_async(prompt)
        except Exception as e:
            # Log the error and provide a user-friendly message
            print(f"Error getting response from LLM: {e}")
            assistant_response = "I'm sorry, I encountered an error while processing your request."

        # The response from this method should be a simple string already.
        response_text = str(assistant_response)

        # 5. Store AI response
        self.db_manager.add_message(session_id, 'assistant', response_text)
        self.db_manager.add_memory(session_id, response_text, metadata={'role': 'assistant'})

        # 6. Return the response
        return response_text

    def _build_prompt(self, memories, history, new_message):
        """Builds the final prompt string for the LLM."""
        prompt_parts = []

        prompt_parts.append("### System Prompt")
        prompt_parts.append("You are Sophia, a helpful AI assistant. Your goal is to provide accurate and relevant information. Here's some context to help you with your response.")
        prompt_parts.append("\n### Relevant Memories (from past conversations)")
        if memories:
            for i, mem in enumerate(memories):
                prompt_parts.append(f"Memory {i+1}: {mem}")
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

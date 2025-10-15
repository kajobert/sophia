from textual.message import Message
from typing import Any

class LogMessage(Message):
    """Zpráva určená pro logovací/stavový widget."""
    def __init__(self, text: str, level: str = "INFO") -> None:
        self.text = text
        self.level = level
        super().__init__()

class ChatMessage(Message):
    """Zpráva určená pro chatovací widget."""
    def __init__(self, content: Any, owner: str, msg_type: str) -> None:
        """
        Args:
            content (Any): Obsah zprávy (může být text, kód atd.).
            owner (str): Vlastník zprávy ('user' nebo 'agent').
            msg_type (str): Typ zprávy ('text', 'markdown', 'tool_code', 'tool_output').
        """
        self.content = content
        self.owner = owner
        self.msg_type = msg_type
        super().__init__()
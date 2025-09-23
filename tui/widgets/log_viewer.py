from textual.widgets import RichLog


class LogViewer(RichLog):
    """A widget to display log messages from Sophia's core."""

    def __init__(self, **kwargs) -> None:
        super().__init__(highlight=True, markup=True, **kwargs)
        self.border_title = "Sophia Core Logs"

    def add_log_message(self, message: str) -> None:
        """Adds a message to the log."""
        self.write(message)

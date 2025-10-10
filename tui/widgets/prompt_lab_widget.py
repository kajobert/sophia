import asyncio
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Static, RichLog
from textual.widget import Widget
from textual.widgets import TextArea

class PromptLabWidget(Widget):
    """Widget for comparing two system prompts."""

    DEFAULT_CSS = """
    .text-area-container {
        height: 15;
        border: solid $primary;
    }
    #user_prompt_input {
        height: 5;
        border: solid $primary;
    }
    #results_container {
        height: 40;
    }
    #result1_container, #result2_container {
        width: 50%;
        height: 100%;
        border: solid $primary;
    }
    """

    def __init__(self, manager):
        super().__init__()
        self.manager = manager

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        yield Static("System Prompt 1", classes="label")
        yield TextArea(id="prompt1_input", classes="text-area-container")
        yield Static("System Prompt 2", classes="label")
        yield TextArea(id="prompt2_input", classes="text-area-container")
        yield Static("User Prompt", classes="label")
        yield TextArea(id="user_prompt_input")
        yield Button("Run Comparison", id="run_comparison")
        with Horizontal(id="results_container"):
            with Vertical(id="result1_container"):
                yield Static("Output 1", classes="label")
                yield RichLog(id="output1", highlight=True, markup=True)
            with Vertical(id="result2_container"):
                yield Static("Output 2", classes="label")
                yield RichLog(id="output2", highlight=True, markup=True)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the button press event."""
        if event.button.id == "run_comparison":
            prompt1 = self.query_one("#prompt1_input", TextArea).text
            prompt2 = self.query_one("#prompt2_input", TextArea).text
            user_prompt = self.query_one("#user_prompt_input", TextArea).text

            if not user_prompt:
                self.query_one("#output1", RichLog).write("User prompt cannot be empty.")
                self.query_one("#output2", RichLog).write("User prompt cannot be empty.")
                return

            output1_log = self.query_one("#output1", RichLog)
            output2_log = self.query_one("#output2", RichLog)

            output1_log.clear()
            output2_log.clear()

            output1_log.write("Running...")
            output2_log.write("Running...")

            # Run the comparisons in parallel
            results = await asyncio.gather(
                self.manager.handle_user_input(user_prompt, system_prompt=prompt1),
                self.manager.handle_user_input(user_prompt, system_prompt=prompt2)
            )

            output1_log.clear()
            output1_log.write(results[0])

            output2_log.clear()
            output2_log.write(results[1])
import asyncio
import logging
import uuid
from core.context import SharedContext
from core.plugin_manager import PluginManager
from plugins.base_plugin import PluginType

# Basic logging setup for Kernel execution
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Kernel:
    """
    Manages the main lifecycle (Consciousness Loop), state, and orchestrates
    plugin execution.
    """

    def __init__(self):
        self.plugin_manager = PluginManager()
        self.is_running = False

    async def consciousness_loop(self):
        """
        The main, infinite loop that keeps Sophia "conscious".
        """
        self.is_running = True
        session_id = str(uuid.uuid4())
        logger.info(f"New session started with ID: {session_id}")

        # Create a context for this session
        context = SharedContext(
            session_id=session_id,
            current_state="INITIALIZING",
            logger=logging.getLogger(f"session-{session_id[:8]}"),
        )

        while self.is_running:
            try:
                # 1. LISTENING PHASE: Get input from all interface plugins
                context.current_state = "LISTENING"
                interface_plugins = self.plugin_manager.get_plugins_by_type(PluginType.INTERFACE)

                if not interface_plugins:
                    logger.warning("No INTERFACE plugins found. Waiting...")
                    await asyncio.sleep(5)
                    continue

                input_tasks = [asyncio.create_task(p.execute(context)) for p in interface_plugins]

                # Wait for any input to be received
                done, pending = await asyncio.wait(
                    input_tasks, return_when=asyncio.FIRST_COMPLETED
                )

                for task in pending:
                    task.cancel()  # Cancel other pending input tasks

                # Process the result from the first completed task
                if done:
                    context = done.pop().result()
                    if context.user_input:
                        user_input = context.user_input
                        logger.info(f"Received user input: '{user_input}'")
                        # Future phases (THINKING, ACTING, etc.) will be added here.
                        # For now, just print the input and wait for the next one.
                        print(f">>> Sophia received: {user_input}")
                        context.user_input = None  # Clear the input for the next cycle

                await asyncio.sleep(0.1)  # A short pause to prevent high CPU usage

            except asyncio.CancelledError:
                self.is_running = False
                logger.info("Consciousness loop was interrupted.")
            except Exception as e:
                logger.error(f"Unexpected error in consciousness loop: {e}", exc_info=True)
                self.is_running = False

    def start(self):
        """Starts the main consciousness loop."""
        try:
            asyncio.run(self.consciousness_loop())
        except KeyboardInterrupt:
            logger.info("Application terminated by user (Ctrl+C).")

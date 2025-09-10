import datetime
import os

class ShortTermMemory:
    """
    Manages the agent's short-term (episodic) memory by logging events
    to a simple text file.
    """
    def __init__(self, log_file_path: str = "logs/episodic_memory.log"):
        self.log_file_path = log_file_path
        self._ensure_log_file_exists()

    def _ensure_log_file_exists(self):
        """Ensures the log directory and file exist."""
        directory = os.path.dirname(self.log_file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        if not os.path.exists(self.log_file_path):
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                f.write("--- Episodic Memory Log Initialized ---\n")

    def add_event(self, event_description: str):
        """
        Adds a new event to the episodic memory log with a timestamp.

        Args:
            event_description (str): A string describing the event.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {event_description}\n"
        
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error writing to memory log: {e}")

    def get_recent_events(self, num_events: int = 10) -> list[str]:
        """
        Retrieves the last N events from the memory log.

        Args:
            num_events (int): The number of recent events to retrieve.

        Returns:
            list[str]: A list of the most recent event strings.
        """
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            # Return the last num_events lines, excluding the newline character
            return [line.strip() for line in lines[-num_events:]]
        except FileNotFoundError:
            return ["Log file not found."]
        except Exception as e:
            return [f"Error reading from memory log: {e}"]

import sqlite3
import datetime
import os

class EpisodicMemory:
    def __init__(self, db_path='memory/episodic_log.sqlite'):
        self.db_path = db_path
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()

    def create_table(self):
        """Creates the events table if it doesn't exist."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    input TEXT,
                    output TEXT,
                    status TEXT NOT NULL
                )
            """)

    def add_event(self, agent_name: str, action: str, input_data: str, output_data: str, status: str):
        """Adds a new event to the database."""
        timestamp = datetime.datetime.now().isoformat()
        # Ensure input and output are strings
        input_str = str(input_data)
        output_str = str(output_data)

        with self.conn:
            self.conn.execute("""
                INSERT INTO events (timestamp, agent_name, action, input, output, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, agent_name, action, input_str, output_str, status))

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()

    def __del__(self):
        """Ensure the connection is closed when the object is destroyed."""
        self.close()

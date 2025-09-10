from crewai_tools import BaseTool
import os


class CustomFileWriteTool(BaseTool):
    name: str = "File Write Tool"
    description: str = (
        "Writes provided text content to a specified file. Creates the file if it does not exist, and overwrites it if it does. Creates parent directories if they don't exist."
    )

    def _run(self, file_path: str, text: str) -> str:
        """
        Writes the given text to the specified file.

        Args:
            file_path (str): The relative path to the file.
            text (str): The content to write to the file.

        Returns:
            str: A confirmation message of the write operation.
        """
        try:
            # Ensure the directory for the file exists
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)

            return f"Successfully wrote content to '{file_path}'."
        except Exception as e:
            return f"Error writing to file '{file_path}': {e}"

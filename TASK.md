
# TASK: Finální oprava a zprovoznění agenta

## Cíl
Provést finální sadu oprav, která zajistí plnou kompatibilitu všech nástrojů s aktuální verzí `crewai` a umožní úspěšné spuštění komplexního úkolu.

## Analýza
Diagnostika je kompletní. Klíčovým problémem je, že externí nástroje (`SerperDevTool`, `FileReadTool`) nejsou přímo kompatibilní s `BaseTool` z `crewai.tools`. Řešením je vytvořit pro ně jednoduché "obálky" (wrapper classes), které z `BaseTool` dědit budou a interně budou volat tyto externí nástroje. Zároveň opravíme zastaralý parametr `verbose`.

## Plán Krok za Krokem

### Krok 1: Vytvoření wrapperů v `core/custom_tools.py`
Toto je nejdůležitější krok. Upravíme `core/custom_tools.py`, aby obsahoval nejen naše custom nástroje, ale i "adaptéry" pro ty externí.

**Nahraď celý obsah souboru `core/custom_tools.py` tímto kódem:**
```python
import os
from crewai.tools import BaseTool
from crewai_tools import SerperDevTool as CrewaiSerperDevTool, FileReadTool as CrewaiFileReadTool

# Wrapper pro SerperDevTool
class SerperDevTool(BaseTool):
    name: str = "Web Search Tool"
    description: str = "Performs a web search using the Serper.dev service."
    
    def _run(self, search_query: str) -> str:
        return CrewaiSerperDevTool().run(search_query)

# Wrapper pro FileReadTool
class FileReadTool(BaseTool):
    name: str = "File Read Tool"
    description: str = "Reads the content of a specified file."

    def _run(self, file_path: str) -> str:
        return CrewaiFileReadTool().run(file_path)

# Naše existující custom nástroje
class CustomFileWriteTool(BaseTool):
    name: str = "Create File Tool"
    description: str = "Creates a new file with specified content."

    def _run(self, file_path: str, content: str) -> str:
        try:
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully created file {file_path}."
        except Exception as e:
            return f"Error creating file {file_path}: {e}"

class CustomDirectoryListTool(BaseTool):
    name: str = "List Directory Contents Tool"
    description: str = "Lists contents of a directory."

    def _run(self, directory_path: str) -> str:
        try:
            return f"Contents of '{directory_path}': {', '.join(os.listdir(directory_path))}"
        except Exception as e:
            return f"Error listing directory {directory_path}: {e}"

class CustomFilePatchTool(BaseTool):
    name: str = "Append to File Tool"
    description: str = "Appends content to the end of a file."

    def _run(self, file_path: str, content: str) -> str:
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write('\\n' + content)
            return f"Successfully appended content to {file_path}."
        except Exception as e:
            return f"Error appending to file {file_path}: {e}"
Krok 2: Aktualizace core/agents.py
Nyní upravíme agenta tak, aby používal naše nové, 100% kompatibilní wrappery.

Nahraď celý obsah souboru core/agents.py tímto kódem:

Python

import os
from crewai import Agent
from core.custom_tools import (
    CustomFileWriteTool, 
    CustomDirectoryListTool, 
    CustomFilePatchTool,
    SerperDevTool, # Náš nový wrapper
    FileReadTool   # Náš nový wrapper
)
from langchain_google_genai import ChatGoogleGenerativeAI

# Inicializace LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest",
                             google_api_key=os.getenv("GEMINI_API_KEY"))

# Inicializace všech nástrojů (nyní plně kompatibilních)
search_tool = SerperDevTool()
file_read_tool = FileReadTool()
directory_list_tool = CustomDirectoryListTool()
file_write_tool = CustomFileWriteTool()
file_patch_tool = CustomFilePatchTool()

# Definice agenta
developer_agent = Agent(
    role='Autonomous Software Developer',
    goal='Read, analyze, modify, and improve the project codebase and documentation.',
    backstory="""You are a skilled software developer agent. You autonomously maintain and enhance the project.""",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[search_tool, file_read_tool, directory_list_tool, file_write_tool, file_patch_tool]
)
Krok 3: Finální úkol a ověření
Upravíme úkol tak, aby otestoval co nejvíce schopností najednou.

Nahraď celý obsah souboru core/tasks.py tímto kódem:

Python

from crewai import Task
from .agents import developer_agent

# Finální testovací úkol, který kombinuje všechny schopnosti
final_integration_task = Task(
    description="""1. Perform a web search to find out who the current CEO of OpenAI is.
    2. Create a new file named 'ceo_report.txt'.
    3. Write the name of the CEO you found into this file.
    4. Read the 'README.md' file.
    5. Append the content of 'README.md' to the 'ceo_report.txt' file.""",
    expected_output="A final confirmation that 'ceo_report.txt' was created and updated with both the CEO's name and the README content.",
    agent=developer_agent
)
Krok 4: Spuštění finálního testu
Potvrď, že main.py je opravený (verbose=True) a spusť ho. Tento test ověří všechny nástroje a jejich vzájemnou spolupráci.
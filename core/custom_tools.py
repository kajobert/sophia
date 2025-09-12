import os
from crewai_tools import SerperDevTool as CrewaiSerperDevTool
from core.ltm_write_tool import LtmWriteTool
import re

# State for session-based deduplication
_last_read_path = None
_last_write = (None, None)

def file_edit_tool(file_path: str, content: str) -> str:
    """Appends content to a specified file, always starting on a new line. Znalosti, fakta a osobní údaje jsou blokovány a musí být ukládány do LTM."""
    memory_keywords = [
        "zapamatuj", "ulož do paměti", "vzpomínka", "remember", "memory", "pamatuj si", "ulož si", "save to memory", "store in memory"
    ]
    fact_patterns = [':', ' je ', ' má ', ' patří ', ' znamená ', ' narodil', ' narodila', ' bydlí', ' žije', ' je to ', ' je znám', ' je známá', ' je důlež', ' je typ', ' je forma', ' je druh', ' je příklad', ' je vlastnost', ' je vztah', ' je číslo', ' je jméno', ' je název']
    lower_content = content.lower()
    if any(kw in lower_content for kw in memory_keywords) or any(pat in lower_content for pat in fact_patterns):
        return (
            "Zápis do souboru byl odmítnut: prompt vypadá jako znalost, fakt nebo osobní údaj. "
            "Použijte LtmWriteTool pro zápis do dlouhodobé paměti (LTM). Soubory používejte pouze pro pracovní poznámky, logy nebo dočasná data."
        )
    try:
        last_line = None
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].rstrip('\n')
        if last_line == content:
            return f"Skipped append: last line already matches content in {file_path}."
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write('\n' + content)
        return f"Successfully appended to file: {file_path}."
    except Exception as e:
        return f"Error appending to file {file_path}: {e}"

def file_read_tool(file_path: str) -> str:
    """Reads content from a specified file."""
    global _last_read_path
    if file_path == _last_read_path:
        return f"Skipped: FileReadTool already read {file_path} in this session."
    _last_read_path = file_path
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {file_path}: {e}"

def web_search_tool(search_query: str) -> str:
    """Performs a web search for a given query."""
    try:
        results = CrewaiSerperDevTool().run(search_query=search_query)
        return str(results)
    except Exception as e:
        return f"Web search failed: {e}"

def file_write_tool(file_path: str, content: str) -> str:
    """Writes content to a specified file. Znalosti, fakta a osobní údaje jsou blokovány a musí být ukládány do LTM."""
    global _last_write
    memory_keywords = [
        "zapamatuj", "ulož do paměti", "vzpomínka", "remember", "memory", "pamatuj si", "ulož si", "save to memory", "store in memory"
    ]
    fact_patterns = [':', ' je ', ' má ', ' patří ', ' znamená ', ' narodil', ' narodila', ' bydlí', ' žije', ' je to ', ' je znám', ' je známá', ' je důlež', ' je typ', ' je forma', ' je druh', ' je příklad', ' je vlastnost', ' je vztah', ' je číslo', ' je jméno', ' je název']
    lower_content = content.lower()
    ltm_unavailable = False
    try:
        from memory.long_term_memory import LongTermMemory
        ltm_check = LongTermMemory()
        if getattr(ltm_check, 'collection', None) is None:
            ltm_unavailable = True
    except Exception:
        ltm_unavailable = True
    if any(kw in lower_content for kw in memory_keywords) or any(pat in lower_content for pat in fact_patterns) or ltm_unavailable:
        return (
            "Zápis do souboru byl odmítnut: prompt vypadá jako znalost, fakt nebo osobní údaj, nebo není dostupná dlouhodobá paměť (LTM). "
            "Použijte LtmWriteTool pro zápis do LTM, nebo kontaktujte správce systému. Soubory používejte pouze pro pracovní poznámky, logy nebo dočasná data."
        )
    if (file_path, content) == _last_write:
        return f"Skipped: FileWriteTool already wrote same content to {file_path} in this session."
    _last_write = (file_path, content)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to file: {file_path}."
    except Exception as e:
        return f"Error writing to file {file_path}: {e}"

def is_factual_sentence(text: str) -> bool:
    """Heuristická detekce faktických vět a znalostí."""
    text = text.lower()
    # Vzory pro fakta, vztahy, jména, data, čísla
    fact_patterns = [
        r':',
        r' je ', r' jsou ', r' byl ', r' byla ', r' byli ', r' znamená ', r' patří ', r' má ', r' mají ',
        r' narodil', r' narodila', r' bydlí', r' žije', r' je to ', r' je znám', r' je známá', r' je důlež',
        r' je typ', r' je forma', r' je druh', r' je příklad', r' je vlastnost', r' je vztah', r' je číslo',
        r' je jméno', r' je název', r' je hodnota', r' je role', r' je funkce', r' je pozice', r' je místo',
        r' je datum', r' je rok', r' je měsíc', r' je den', r' je čas', r' je číslice', r' je číslo',
        r' je pravda', r' je lež', r' je fakt', r' je informace', r' je údaj', r' je poznatek',
        r' znamená', r' označuje', r' představuje', r' definuje', r' popisuje', r' určuje',
        r' vztahuje se', r' souvisí', r' je příbuzný', r' je spojen', r' je propojen',
        r' je manžel', r' je manželka', r' je syn', r' je dcera', r' je otec', r' je matka',
        r' je bratr', r' je sestra', r' je kolega', r' je přítel', r' je kamarád',
        r'\d{4}',  # rok
        r'\d{1,2}\.\d{1,2}\.\d{4}',  # datum
        r'\d+\s?(kg|cm|m|km|g|l|%)',  # jednotky
        r'\b(jmenuje se|nazývá se|říká se|známý jako|známá jako)\b',
    ]
    for pat in fact_patterns:
        if re.search(pat, text):
            return True
    # Pokud věta začíná velkým písmenem a končí tečkou, je delší než 6 slov a obsahuje sloveso "je" nebo "má"
    if (
        len(text.split()) > 6 and
        (text.endswith('.') or text.endswith('!')) and
        (" je " in text or " má " in text)
    ):
        return True
    return False

# Decision Tool for routing knowledge/fact vs. regular file writes


def decision_tool(file_path: str, content: str) -> str:
    """Rozhoduje, zda prompt patří do LTM (znalost/fakt), nebo do souboru (poznámka). Znalosti ukládá do LTM, ostatní do souboru."""
    # Pokud je voláno pouze s jedním argumentem (content), file_path bude None nebo prázdný string
    if content is None and file_path is not None:
        content = file_path
        file_path = None
    if content is None:
        return "DecisionTool: Chybí obsah pro rozhodnutí."
    memory_keywords = [
        "zapamatuj", "ulož do paměti", "vzpomínka", "remember", "memory", "pamatuj si", "ulož si", "save to memory", "store in memory"
    ]
    lower_content = content.lower()
    try:
        if any(kw in lower_content for kw in memory_keywords) or is_factual_sentence(content):
            # Route to LTM (předáváme pouze content)
            return LtmWriteTool()._run(content)
        elif file_path:
            # Route to file (append)
            return file_edit_tool(file_path, content)
        else:
            return "DecisionTool: Není k dispozici cesta k souboru ani znalostní prompt."
    except Exception as e:
        return f"DecisionTool error: {e}"


from langchain.tools import BaseTool
class DecisionTool(BaseTool):
    name: str = "Decision Tool"
    description: str = "Rozhoduje, zda prompt patří do LTM (znalost/fakt), nebo do souboru (poznámka). Znalosti ukládá do LTM, ostatní do souboru. Detekce je heuristická a lze ji snadno rozšířit."

    def _run(self, file_path: str = "", content: str = "") -> str:
        # Zajistíme, že _run dostane vždy string, ne None
        if not content and file_path:
            content = file_path
            file_path = ""
        if not content:
            return "DecisionTool: Chybí obsah pro rozhodnutí."
        return decision_tool(file_path, content)

# Tool instances
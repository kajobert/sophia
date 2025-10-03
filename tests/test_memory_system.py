import os
import sys
import pytest
import shutil

# Přidání cesty k projektu pro importy
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from core.long_term_memory import LongTermMemory
from core.prompt_builder import PromptBuilder

# Defiujeme cestu k testovací databázi
TEST_DB_PATH = os.path.join(project_root, "tests/test_db/chroma")
TEST_CONFIG_PATH = os.path.join(project_root, "config/config.yaml")

@pytest.fixture(scope="module")
def memory_system():
    """
    Pytest fixtura, která jednou pro celý modul vytvoří instanci LTM
    a po skončení všech testů smaže testovací databázi.
    """
    # Vyčištění předchozích běhů pro jistotu
    if os.path.exists(TEST_DB_PATH):
        shutil.rmtree(TEST_DB_PATH)

    ltm = LongTermMemory(
        project_root=project_root,
        db_path_override=TEST_DB_PATH,
        collection_name_override="test_collection_module"
    )
    builder = PromptBuilder(
        system_prompt_path=os.path.join(project_root, "prompts/system_prompt.txt"),
        ltm=ltm,
        short_term_limit=2,
        long_term_retrieval_limit=1
    )

    yield ltm, builder

    # Úklid po VŠECH testech v modulu
    ltm.shutdown()
    if os.path.exists(TEST_DB_PATH):
        shutil.rmtree(TEST_DB_PATH)


def test_ltm_add_and_search(memory_system):
    """
    Testuje základní funkčnost LTM: přidání a následné vyhledání záznamu.
    """
    ltm, _ = memory_system

    # Vyčistíme paměť pro jistotu
    ltm.clear_memory()

    # Přidáme dva odlišné záznamy
    ltm.add_memory("První záznam se týká opravy chyby v přihlašování.")
    ltm.add_memory("Druhý záznam popisuje nasazení nové verze na produkci.")

    # Prohledáme paměť s dotazem, který je sémanticky blízko prvnímu záznamu
    results = ltm.search_memory("Jak opravit login?", n_results=1)

    assert len(results) == 1
    assert "přihlašování" in results[0]
    assert "produkci" not in results[0]


def test_prompt_builder_rag_integration(memory_system):
    """
    Integrační test, který ověřuje, že PromptBuilder správně používá RAG
    k sestavení finálního promptu.
    """
    ltm, builder = memory_system
    ltm.clear_memory()

    # 1. Naplníme LTM historickými daty
    ltm.add_memory("Historický záznam: Uživatel v minulosti často řešil problémy s výkonem databáze.")
    ltm.add_memory("Historický záznam: Dříve byla chyba v API pro fakturaci, která byla opravena.")
    ltm.add_memory("Historický záznam: Klíčová komponenta pro notifikace byla přepsána v Rustu.")

    # 2. Vytvoříme krátkodobou historii (poslední kroky)
    short_term_history = [
        ("Akce 1: list_files()", "Výsledek: main.py, db_connector.py, ..."),
        ("Akce 2: read_file('db_connector.py')", "Výsledek: # Tento soubor obsahuje staré a pomalé SQL dotazy.")
    ]

    # 3. Sestavíme prompt
    prompt = builder.build_prompt("Popis nástrojů zde", short_term_history)

    # 4. Ověříme výsledek
    # Očekáváme, že RAG najde paměť o výkonu databáze
    assert "# **RELEVANTNÍ KONTEXT Z ARCHIVU**" in prompt
    assert "problémy s výkonem databáze" in prompt

    # Zároveň by neměl obsahovat nerelevantní paměť o fakturaci nebo notifikacích
    assert "fakturaci" not in prompt
    assert "Rustu" not in prompt

    # Zkontrolujeme, zda je v promptu správně zahrnuta krátkodobá historie
    assert "# **NEDÁVNÁ HISTORIE (PRACOVNÍ PAMĚŤ)**" in prompt
    assert "staré a pomalé SQL dotazy" in prompt

    # Ověříme, že finální instrukce odkazují na oba kontexty
    assert "Analyzuj KONTEXT Z ARCHIVU a NEDÁVNOU HISTORII" in prompt


def test_prompt_builder_empty_ltm(memory_system):
    """
    Testuje, že PromptBuilder funguje správně, i když je LTM prázdná.
    """
    ltm, builder = memory_system
    ltm.clear_memory()

    short_term_history = [
        ("Akce: prvni_krok()", "Výsledek: OK")
    ]

    prompt = builder.build_prompt("Nástroje", short_term_history)

    # Neočekáváme sekci s relevantním kontextem
    assert "# **RELEVANTNÍ KONTEXT Z ARCHIVU**" not in prompt
    assert "# **NEDÁVNÁ HISTORIE (PRACOVNÍ PAMĚŤ)**" in prompt
    assert "prvni_krok()" in prompt
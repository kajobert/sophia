# /memory/advanced_memory.py
"""
Modul pro správu pokročilé paměti Sophie.
Tento modul je wrapper okolo knihovny GibsonAI/memori a poskytuje
jednotné rozhraní pro epizodickou a sémantickou paměť.
"""

import yaml
from memori import Memori
from datetime import datetime
from sqlalchemy import text

class AdvancedMemory:
    """
    Třída pro správu paměti pomocí knihovny Memori.
    """
    def __init__(self, config_path='config.yaml', user_id="sophia"):
        """
        Inicializuje knihovnu Memori s připojením k databázi
        a nastaví potřebné proměnné.
        """
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        db_config = config['database']
        db_conn_str = f"postgresql://{db_config['db_user']}:{db_config['db_password']}@{db_config['db_host']}:{db_config['db_port']}/{db_config['db_name']}"

        # Zatím nevíme, jaké API klíče jsou potřeba, ale Memori je vyžaduje.
        # Použijeme dummy hodnoty, pokud nejsou v configu.
        api_key = config.get('openai_api_key', 'sk-dummy')

        self.user_id = user_id
        self.memori = Memori(
            database_connect=db_conn_str,
            openai_api_key=api_key,
            # Použijeme kombinovaný mód pro nejlepší výsledky
            conscious_ingest=True,
            auto_ingest=True,
            namespace=self.user_id # Izolace paměti pro různé uživatele/agenty
        )
        # Aktivace automatického zaznamenávání (pokud budeme používat)
        self.memori.enable()
        print("AdvancedMemory initialized.")

    def add_memory(self, content, mem_type, metadata=None):
        """
        Přidá novou vzpomínku do Memori tím, že zaznamená "konverzaci"
        s jedním uživatelským vstupem.

        Args:
            content (str): Obsah vzpomínky.
            mem_type (str): Typ vzpomínky (např. 'user_interaction', 'self_reflection').
            metadata (dict, optional): Další metadata k uložení.

        Returns:
            str: ID nově zaznamenané konverzace.
        """
        if metadata is None:
            metadata = {}

        # Přidáme typ paměti do metadat pro pozdější filtrování
        metadata['memory_type'] = mem_type

        # Simulujeme konverzaci, kde uživatel něco řekne a AI jen potvrdí.
        # Tímto způsobem využijeme interní logiku Memori pro zpracování.
        chat_id = self.memori.record_conversation(
            user_input=content,
            ai_output=f"Noted: {mem_type}", # Jednoduchá odpověď pro záznam
            model="internal_event",
            metadata=metadata
        )
        return chat_id

    def access_memory(self, memory_id):
        """
        Načte vzpomínku z databáze. Zvýšení váhy je řešeno interně
        knihovnou Memori na základě přístupu.

        Args:
            memory_id (str): ID konverzace (vzpomínky).

        Returns:
            dict: Slovník s daty vzpomínky, nebo None.
        """
        # Memori nemá přímou metodu pro přístup k jedné paměti podle ID.
        # Použijeme get_conversation_history a vyfiltrujeme podle ID.
        history = self.memori.get_conversation_history(limit=1000) # Omezení, může být potřeba upravit
        for memory in history:
            if memory.get('chat_id') == memory_id:
                return memory
        return None

    def read_last_n_memories(self, n=10):
        """
        Přečte posledních N vzpomínek (konverzací).

        Args:
            n (int): Počet vzpomínek k načtení.

        Returns:
            list: Seznam slovníků s daty posledních N vzpomínek.
        """
        return self.memori.get_conversation_history(limit=n)

    def add_task(self, description):
        """
        Přidá nový úkol do paměti.

        Args:
            description (str): Popis úkolu.

        Returns:
            str: ID nově přidaného úkolu.
        """
        return self.add_memory(description, "TASK", metadata={'status': 'new'})

    def get_next_task(self):
        """
        Najde nejstarší nový úkol, označí ho jako probíhající a vrátí ho.
        """
        # Hledáme paměti s typem 'TASK'.
        # Poznámka: Memori nemá přímý způsob, jak filtrovat podle metadat,
        # takže musíme načíst všechny úkoly a filtrovat je v Pythonu.
        tasks = self.memori.db_manager.search_memories(
            query="", # Prázdný dotaz pro načtení všech
            namespace=self.user_id,
            category_filter=['TASK'],
            limit=100 # Načteme více úkolů pro případ, že je mnoho hotových
        )

        # Najdeme nejstarší úkol se statusem 'new'
        next_task = None
        for task in sorted(tasks, key=lambda x: x.get('timestamp')):
            metadata = task.get('metadata', {})
            if metadata.get('status') == 'new':
                next_task = task
                break

        if next_task:
            task_id = next_task.get('chat_id')
            self.update_task_status(task_id, "IN_PROGRESS")
            # Načteme úkol znovu, abychom měli aktuální stav
            return self.access_memory(task_id)

        return None

    def update_task_status(self, task_id, status):
        """
        Aktualizuje stav úkolu pomocí přímého SQL dotazu.

        Args:
            task_id (str): ID úkolu (chat_id).
            status (str): Nový stav.
        """
        # Toto je nejsložitější část, protože Memori nemá veřejné API pro update.
        # Musíme použít přímý SQL dotaz.
        # Cílová tabulka je 'chat_history' a sloupec 'metadata_json'.

        # Nejprve načteme stávající metadata
        task_memory = self.access_memory(task_id)
        if not task_memory:
            return

        metadata = task_memory.get('metadata', {})
        metadata['status'] = status

        # Aktualizujeme JSONB sloupec v PostgreSQL
        # Použijeme specifickou syntaxi pro JSONB: `jsonb_set`
        # Pro SQLite a MySQL by byla potřeba jiná syntaxe.
        # Zaměřujeme se na PostgreSQL, protože to je databáze projektu.

        query = text("""
            UPDATE chat_history
            SET metadata_json = jsonb_set(metadata_json::jsonb, '{status}', :status::jsonb)
            WHERE chat_id = :chat_id
        """)

        self.memori.db_manager.execute_with_translation(
            query,
            parameters={'status': f'"{status}"', 'chat_id': task_id}
        )

    def close(self):
        """
        Placeholder pro případné uzavření zdrojů.
        Knihovna Memori podle dokumentace neukazuje explicitní metodu pro uzavření.
        """
        print("AdvancedMemory closed.")
        pass

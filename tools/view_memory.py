import argparse
import sys
import os
from rich.console import Console
from rich.table import Table

# Přidání cesty k `core` modulu, aby bylo možné importovat MemoryManager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.memory_manager import MemoryManager

def display_memories(memories: list[dict]):
    """
    Zobrazí seznam vzpomínek v přehledné tabulce pomocí knihovny rich.
    """
    if not memories:
        console.print("[yellow]Nebyly nalezeny žádné vzpomínky odpovídající zadaným kritériím.[/yellow]")
        return

    table = Table(title="🧠 Agent's Memories", show_header=True, header_style="bold magenta")
    table.add_column("Timestamp", style="dim", width=20)
    table.add_column("Task", style="cyan", no_wrap=False)
    table.add_column("Summary", style="green", no_wrap=False)

    for mem in memories:
        table.add_row(
            str(mem['timestamp']),
            mem['task'],
            mem['summary']
        )

    console.print(table)


def main():
    """
    Hlavní funkce pro spuštění nástroje pro zobrazení vzpomínek.
    """
    parser = argparse.ArgumentParser(
        description="Nástroj pro zobrazení a prohledávání paměti agenta.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "keywords",
        nargs='*',
        help="Klíčová slova pro vyhledávání ve vzpomínkách (v souhrnech úkolů)."
    )
    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=10,
        help="Maximální počet zobrazených vzpomínek (default: 10)."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Zobrazit všechny vzpomínky (až do limitu), ignoruje klíčová slova."
    )

    args = parser.parse_args()

    global console
    console = Console()

    memory = MemoryManager()
    memories = []

    try:
        if args.all:
            console.print(f"[bold blue]Zobrazuji všech (až {args.limit}) vzpomínek...[/bold blue]")
            memories = memory.get_all_memories(limit=args.limit)
        elif args.keywords:
            console.print(f"[bold blue]Vyhledávám vzpomínky s klíčovými slovy: [italic]{args.keywords}[/italic]...[/bold blue]")
            memories = memory.get_relevant_memories(keywords=args.keywords, limit=args.limit)
        else:
            console.print(f"[bold blue]Nezadána žádná klíčová slova. Zobrazuji {args.limit} nejnovějších vzpomínek...[/bold blue]")
            memories = memory.get_all_memories(limit=args.limit)

        display_memories(memories)

    except Exception as e:
        console.print(f"[bold red]Došlo k chybě: {e}[/bold red]")
    finally:
        memory.close()


if __name__ == "__main__":
    main()
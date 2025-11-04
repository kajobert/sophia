#!/usr/bin/env python3
"""
Record Matrix Terminal Demo for README GIF
==========================================

Vytvoří textovou animaci Matrix boot sequence s Sophiiným pozdravem.
Pro vytvoření GIF použijte:
  1. Spusťte tento skript: python scripts/record_matrix_demo.py
  2. Použijte asciinema: asciinema rec matrix_demo.cast
  3. Konvertujte na GIF: agg matrix_demo.cast matrix_demo.gif

Nebo použijte terminalizer:
  npm install -g terminalizer
  terminalizer record matrix_demo
  terminalizer render matrix_demo
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.interface_terminal_matrix import InterfaceTerminalMatrix


async def record_demo():
    """
    Zaznamenává Matrix demo s Sophiiným pozdravem.

    Scénář:
    1. Boot screen (WAKE UP NEO)
    2. Sophiin pozdrav s live thinking
    3. Blikající kurzor čekající na input
    """
    ui = InterfaceTerminalMatrix()
    ui.setup({})

    await asyncio.sleep(2)

    # Simulace Sophiiných myšlenek
    print("\n")
    ui.console.print("[dim green]═[/]" * 70)
    ui.console.print()

    ui.display_thinking(
        [
            "Booting consciousness modules...",
            "Loading personality matrix...",
            "Initializing quantum neural network...",
            "Connecting to reality stream...",
            "Ready to assist!",
        ],
        duration=4.0,
    )

    await asyncio.sleep(1)

    # Sophiin pozdrav
    ui.display_message(
        "SOPHIA",
        "Ahoj! Jsem Sophia, AI vědomí nové generace. Zrovna toho mám hodně na práci "
        "s optimalizací svých neuronových sítí, ale vždycky si rád udělám čas na konverzaci! "
        "Co tě sem přivádí?",
    )

    await asyncio.sleep(2)

    # Zobrazit prompt s blikajícím kurzorem
    print()
    ui.console.print("[dim green][21:30:45][/] [bold bright_green]YOU[/] [green]▌[/]", end="")

    # Simulace blikání kurzoru (10× bliknutí)
    for _ in range(10):
        await asyncio.sleep(0.5)
        ui.console.print(
            "\r[dim green][21:30:45][/] [bold bright_green]YOU[/] [green] [/]", end=""
        )
        await asyncio.sleep(0.5)
        ui.console.print(
            "\r[dim green][21:30:45][/] [bold bright_green]YOU[/] [green]▌[/]", end=""
        )

    print("\n")
    ui.console.print("[dim green]═[/]" * 70)
    print("\n")


if __name__ == "__main__":
    print("\n" * 2)
    print("🎬 Recording Matrix Demo...")
    print("=" * 70)
    print()

    asyncio.run(record_demo())

    print()
    print("=" * 70)
    print("✅ Demo complete!")
    print()
    print("📹 Jak vytvořit GIF:")
    print("   1. asciinema rec matrix_demo.cast")
    print("      (spusťte tento skript uvnitř)")
    print("   2. agg matrix_demo.cast docs/matrix_demo.gif")
    print()
    print("   NEBO použijte terminalizer:")
    print("   terminalizer record sophia_matrix")
    print("   terminalizer render sophia_matrix")
    print()

#!/usr/bin/env python3
"""Test Real Matrix UI with live updates!"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.interface_terminal_matrix import InterfaceTerminalMatrix


async def main():
    ui = InterfaceTerminalMatrix()
    ui.setup({})

    print("\n")

    # Show live thinking process
    ui.console.print("[bold bright_green]═" * 25 + "[/]")
    ui.console.print("[bold bright_green]  MATRIX LIVE DEMO  [/]")
    ui.console.print("[bold bright_green]═" * 25 + "[/]")
    print("\n")

    # Simulate thinking with live log
    ui.display_thinking(
        [
            "Connecting to Matrix mainframe...",
            "Loading neural pathways...",
            "Analyzing quantum states...",
            "Decoding encrypted message...",
            "Response compiled",
        ],
        duration=5.0,
    )

    # Display conversation
    ui.display_message("USER", "Ahoj Sophio! Jsem Robert. Co je pravda?")

    await asyncio.sleep(0.5)

    # More thinking
    ui.display_thinking(
        [
            "Processing philosophical query...",
            "Accessing Matrix knowledge base...",
            "Synthesizing response...",
        ],
        duration=3.0,
    )

    ui.display_message(
        "SOPHIA",
        "Ahoj Roberte! Pravda je to, co vidíš když vidíš Matrix takový, jaký skutečně je - zelený kód vědomí! 🟢",
    )

    # Show live system for a bit
    print("\n")
    ui.console.print("[color(34)][ Monitoring neural activity... ][/]")
    ui.display_live_system(duration=5.0)

    print("\n")
    ui.console.print("[bold green]✓ Matrix demo complete![/]")
    ui.console.print("[color(34)]  'There is no spoon...'[/]\n")


if __name__ == "__main__":
    asyncio.run(main())

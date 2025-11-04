#!/usr/bin/env python3
"""
Quick test for Matrix SOPHIA conversation
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from plugins.interface_terminal_matrix import InterfaceTerminalMatrix


async def main():
    ui = InterfaceTerminalMatrix()
    ui.setup({})

    print("\n")
    ui.console.print("[bold bright_green]═" * 26 + "[/]")
    ui.console.print("[bold bright_green]  MATRIX CONVERSATION TEST  [/]")
    ui.console.print("[bold bright_green]═" * 26 + "[/]")
    print("\n")

    # Simulate conversation
    ui.display_message("USER", "Ahoj Sophio! Jsem Robert. Jak se máš?")

    # Simulate thinking
    ui.console.print()

    def response_gen():
        response = "Ahoj Roberte! Vítej v Matrixu! Cítím se skvěle - všechny systémy jsou online a zelené. Je mi potěšením tě poznat! 🟢"
        for char in response:
            yield char

    ui.current_model = "MATRIX-AI-v3.14"
    ui.display_message_stream(
        "SOPHIA", response_gen(), tokens=1200, cost=0.0156, response_time=1.8
    )

    print("\n")
    ui.console.print("[bold green]✓ Matrix conversation complete![/]")
    ui.console.print("[dim green]  'There is no spoon...'[/]\n")


if __name__ == "__main__":
    asyncio.run(main())

import pytest
from unittest.mock import patch
import asyncio

# Musíme patchnout SophiaController, aby se nesnažil spustit subprocess
# a připojit se k reálné databázi během testů.


# Musíme patchnout SophiaController, aby se nesnažil spustit subprocess
# a připojit se k reálné databázi během testů.
@pytest.mark.asyncio
@patch("tui.app.SophiaController")
async def test_tui_app_startup_and_shutdown(mock_controller):
    """
    Testuje, zda se TUI aplikace dokáže spustit a ukončit bez chyby.
    """
    from tui.app import SophiaTUI

    # Nastavení mocku, aby se choval jako reálný controller
    mock_instance = mock_controller.return_value
    # Mockujeme asynchronní metody
    mock_instance.get_task_updates.return_value = asyncio.Future()
    mock_instance.get_task_updates.return_value.set_result([])
    mock_instance.start_sophia_core.return_value = asyncio.Future()
    mock_instance.start_sophia_core.return_value.set_result(None)

    app = SophiaTUI()

    # run_test je speciální metoda od Textual pro testování
    # Aplikaci necháme běžet na pozadí a poté ji ukončíme
    async with app.run_test() as pilot:
        # Počkáme krátký okamžik, aby se stihly spustit on_mount a další úvodní eventy
        await pilot.pause(0.1)

    # Ověříme, že se aplikace pokusila spustit jádro při startu
    mock_instance.start_sophia_core.assert_called_once()

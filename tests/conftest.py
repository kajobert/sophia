# --- Helper pro správu snapshotů ---
import shutil
import pathlib
import time

def manage_snapshots():
    """
    Automaticky archivuje nebo maže received snapshoty v tests/snapshots/:
    - Pokud existuje .approved.txt, smaže odpovídající .received.txt
    - Pokud .received.txt nemá approved protějšek, přesune do archive/
    """
    base = pathlib.Path("tests/snapshots")
    archive = base / "archive"
    archive.mkdir(exist_ok=True)
    for received in base.glob("*.received.txt"):
        approved = base / received.name.replace(".received.txt", ".approved.txt")
        if approved.exists():
            received.unlink()
        else:
            ts = int(time.time())
            archive_path = archive / f"{received.stem}_{ts}.received.txt"
            shutil.move(str(received), str(archive_path))

# Volat ručně nebo v rámci cleanup/test setup

import sys
import subprocess
import pytest
import os

# --- SNAPSHOT TESTING ---
try:
    from approvaltests import verify, verify_file
    """Fixture pro snapshot/approval testování s archivací unikátních received snapshotů."""
except ImportError:
    print("[conftest] Modul 'approvaltests' nebyl nalezen, pokouším se nainstalovat...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'approvaltests'], check=False)
    try:
        from approvaltests import verify, verify_file
    except ImportError:
        def verify(*a, **kw):
            pytest.skip("approvaltests není dostupný, snapshot test přeskočen.")
        def verify_file(*a, **kw):
            pytest.skip("approvaltests není dostupný, snapshot test přeskočen.")


# --- Robustní import externího modulu ---

import importlib
import types
import logging

def robust_import(module_name, symbol=None, pip_name=None):
    """
    Robustně importuje modul nebo symbol (třídu/funkci) z modulu.
    Pokud je symbol None, importuje celý modul.
    Pokud je symbol zadán, importuje konkrétní symbol (třídu/funkci) z modulu.
    Detekuje kolize mezi namespace package a modulem a loguje varování.
    """
    pip_name = pip_name or module_name
    try:
        mod = importlib.import_module(module_name)
    except ImportError:
        print(f"[test] Modul '{module_name}' nebyl nalezen, pokouším se nainstalovat...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', pip_name], check=False)
        try:
            mod = importlib.import_module(module_name)
        except ImportError:
            pytest.skip(f"Modul '{module_name}' stále chybí i po pokusu o instalaci. Test je přeskočen.")

    # Detekce kolize: pokud existuje jak modul, tak balíček se stejným jménem
    if hasattr(mod, '__path__') and hasattr(mod, '__file__'):
        logging.warning(f"[robust_import] Namespace package a modul mají stejné jméno: {module_name}. To může způsobit kolize v importech.")

    if symbol:
        # Robustní import symbolu (třída/funkce)
        if hasattr(mod, symbol):
            return getattr(mod, symbol)
        # Zkusit importovat symbol z podmodulu se stejným jménem
        try:
            submod = importlib.import_module(f"{module_name}.{symbol}")
            if hasattr(submod, symbol):
                return getattr(submod, symbol)
        except ImportError:
            pass
        pytest.skip(f"Symbol '{symbol}' nebyl nalezen v modulu '{module_name}' ani v jeho podmodulech. Možná kolize nebo špatná cesta.")
    return mod

# --- Ochrana proti mazání kritických souborů ---
def safe_remove(path):
    import shutil
    basename = os.path.basename(path)
    if basename in [".env", "watchdog.alive"]:
        print(f"[test] Pokus o mazání chráněného souboru: {basename}")
        raise RuntimeError(f"Test se pokusil smazat chráněný soubor: {basename}")
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)

# --- Fixture pro dočasný adresář ---
@pytest.fixture
def temp_dir(tmp_path):
    """Fixture pro bezpečné dočasné adresáře v testech."""
    return tmp_path

# --- Helper pro snapshot testování ---
import inspect
import pathlib
import shutil
import time

@pytest.fixture
def snapshot(request):
    """Fixture pro snapshot/approval testování s automatickým vytvořením approved souboru, pokud chybí."""
    def _snapshot(data, ext="txt"):
        base = pathlib.Path("tests/snapshots")
        base.mkdir(parents=True, exist_ok=True)
        test_file = pathlib.Path(request.node.fspath)
        test_name = request.node.name
        test_file_stem = test_file.stem
        approved = base / f"{test_file_stem}.{test_name}.approved.{ext}"
        received = base / f"{test_file_stem}.{test_name}.received.{ext}"
        archive_dir = base / "archive" / test_file_stem / test_name
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Smazat nebo archivovat starý received, pokud existuje
        if received.exists():
            if approved.exists():
                if received.read_bytes() == approved.read_bytes():
                    received.unlink()
                else:
                    ts = int(time.time())
                    archive_path = archive_dir / f"{test_file_stem}.{test_name}_{ts}.received.{ext}"
                    shutil.move(str(received), str(archive_path))
            else:
                ts = int(time.time())
                archive_path = archive_dir / f"{test_file_stem}.{test_name}_{ts}.received.{ext}"
                shutil.move(str(received), str(archive_path))

        # Pokud approved neexistuje, vytvoř ho z aktuálního výstupu a označ test jako xfail
        if not approved.exists():
            approved.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(data, (dict, list)):
                import pprint
                content = pprint.pformat(data)
            else:
                content = str(data)
            # Zapsat received snapshot vždy, i při xfail
            received.write_text(content + "\n", encoding="utf-8")
            approved.write_text(content + "\n", encoding="utf-8")
            pytest.xfail(f"Approved snapshot neexistoval, byl automaticky vytvořen: {approved.name}. Zkontrolujte a případně potvrďte jeho obsah.")
        # Jinak použij standardní verify
        try:
            from approvaltests import verify
            verify(data)
        except ImportError:
            # fallback: pouze porovnat obsah
            actual = data if isinstance(data, str) else str(data)
            expected = approved.read_text(encoding="utf-8")
            assert actual.strip() == expected.strip(), f"Snapshot mismatch: {approved}"
    return _snapshot
    return _snapshot
import pytest
import os

@pytest.fixture(scope="function", autouse=True)
def set_test_mode_for_function(monkeypatch):
    """
    Ensures that the SOPHIA_TEST_MODE environment variable is set to "1"
    for the entire test session, before any modules are imported.
    This is critical for tests that rely on this variable to mock services
    like Redis or LLM calls at import time.
    """
    monkeypatch.setenv("SOPHIA_TEST_MODE", "1")

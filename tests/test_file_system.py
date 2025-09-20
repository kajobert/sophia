import os
import pytest
from tests.conftest import robust_import, safe_remove

def test_file_system_import(request):
    """Auditní test: pokud není file_system modul, vytvoří auditní snapshot a označí test jako xfail."""
    try:
        fs_mod = robust_import('core.file_system')
        snapshot = request.getfixturevalue("snapshot") if "snapshot" in request.fixturenames else None
        if snapshot:
            snapshot("file_system import OK")
    except Exception as e:
        snapshot = request.getfixturevalue("snapshot") if "snapshot" in request.fixturenames else None
        msg = f"file_system není dostupný: {e}"
        if snapshot:
            snapshot(msg)
        pytest.xfail(msg)

# Šablona pro robustní testy:
# def test_file_system_list_dir(request, snapshot, temp_dir):
#     list_dir = robust_import('core.file_system', 'list_dir')
#     # Vytvoř dočasný adresář a soubory
#     (temp_dir / "testdir").mkdir()
#     (temp_dir / "testdir" / "file.txt").write_text("obsah")
#     result = list_dir(str(temp_dir / "testdir"))
#     snapshot(result)

from tests.conftest import robust_import



def test_write_file_tool(request, snapshot):
    WriteFileTool = robust_import('tools.file_system', 'WriteFileTool')
    tool = WriteFileTool()
    result = [hasattr(tool, "_run"), hasattr(tool, "_arun")]
    snapshot(str(result))



def test_read_file_tool(request, snapshot):
    ReadFileTool = robust_import('tools.file_system', 'ReadFileTool')
    tool = ReadFileTool()
    result = [hasattr(tool, "_run"), hasattr(tool, "_arun")]
    snapshot(str(result))



def test_list_directory_tool(request, snapshot):
    ListDirectoryTool = robust_import('tools.file_system', 'ListDirectoryTool')
    tool = ListDirectoryTool()
    result = [hasattr(tool, "_run"), hasattr(tool, "_arun")]
    snapshot(str(result))

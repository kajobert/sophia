import os
import shutil
import tempfile
import pytest
from tests.conftest import robust_import, safe_remove

WriteFileTool = robust_import('tools.file_system', 'WriteFileTool')
ReadFileTool = robust_import('tools.file_system', 'ReadFileTool')
ListDirectoryTool = robust_import('tools.file_system', 'ListDirectoryTool')
PathOutsideSandboxError = robust_import('tools.file_system', 'PathOutsideSandboxError')
FileSystemNotFoundError = robust_import('tools.file_system', 'FileSystemNotFoundError')
IsDirectoryError = robust_import('tools.file_system', 'IsDirectoryError')
NotDirectoryError = robust_import('tools.file_system', 'NotDirectoryError')
FileSystemError = robust_import('tools.file_system', 'FileSystemError')
# --- ListDirectoryTool Tests ---
@pytest.fixture
def sandbox_snapshot(request):
    # Každý test má unikátní podadresář podle jména testu
    import pathlib
    test_name = request.node.name.replace("/", "_").replace("[", "_").replace("]", "_")
    sandbox_dir = pathlib.Path("sandbox")
    test_dir = sandbox_dir / "test_fs_data" / f"case_{test_name}"
    test_dir.mkdir(parents=True, exist_ok=True)
    write_tool = WriteFileTool()
    read_tool = ReadFileTool()
    list_tool = ListDirectoryTool()
    yield write_tool, read_tool, list_tool, str(test_dir), test_dir, sandbox_dir
    # Cleanup přes safe_remove
    for f in test_dir.iterdir():
        safe_remove(str(f))
    safe_remove(str(test_dir))


import os
import shutil
import tempfile
import pytest
from tests.conftest import robust_import, safe_remove

WriteFileTool = robust_import('tools.file_system', 'WriteFileTool')
ReadFileTool = robust_import('tools.file_system', 'ReadFileTool')
ListDirectoryTool = robust_import('tools.file_system', 'ListDirectoryTool')
PathOutsideSandboxError = robust_import('tools.file_system', 'PathOutsideSandboxError')
FileSystemNotFoundError = robust_import('tools.file_system', 'FileSystemNotFoundError')
IsDirectoryError = robust_import('tools.file_system', 'IsDirectoryError')
NotDirectoryError = robust_import('tools.file_system', 'NotDirectoryError')
FileSystemError = robust_import('tools.file_system', 'FileSystemError')




# --- Fixtures ---

@pytest.fixture
def sandbox_snapshot(tmp_path):
    # Vytvoř snapshot sandboxu v temp adresáři
    sandbox_dir = tmp_path / "sandbox"
    sandbox_dir.mkdir()
    test_dir = sandbox_dir / "test_fs_data"
    test_dir.mkdir()
    write_tool = WriteFileTool()
    read_tool = ReadFileTool()
    list_tool = ListDirectoryTool()
    yield write_tool, read_tool, list_tool, "test_fs_data", test_dir, sandbox_dir
    # Cleanup přes safe_remove
    for f in test_dir.iterdir():
        safe_remove(str(f))
    safe_remove(str(test_dir))
    safe_remove(str(sandbox_dir))


# --- WriteFileTool Tests ---

@pytest.mark.parametrize("file_path,content,should_succeed,expected_exception", [
    ("test_write.txt", "Hello, Sandbox!", True, None),
    ("../outside_test.txt", "breach", False, PathOutsideSandboxError),
])
def test_write_file(request, sandbox_snapshot, file_path, content, should_succeed, expected_exception, snapshot):
    write_tool, _, _, test_dir_name, test_dir, sandbox_dir = sandbox_snapshot
    # Všechny cesty relativně k sandbox_dir
    if should_succeed:
        rel_path = os.path.relpath((test_dir / file_path), sandbox_dir)
        result = write_tool._run(file_path=rel_path, content=content)
        print(f"[DEBUG] rel_path: {rel_path}")
        print(f"[DEBUG] test_dir: {test_dir}")
        print(f"[DEBUG] sandbox_dir: {sandbox_dir}")
        print(f"[DEBUG] full_path: {test_dir / file_path}")
        # Najdi skutečně vytvořený soubor v sandboxu
        for root, dirs, files in os.walk(sandbox_dir):
            for f in files:
                print(f"[DEBUG] found file: {os.path.join(root, f)}")
        assert "successfully" in result
        full_path = test_dir / file_path
        assert full_path.exists()
        with open(full_path, "r", encoding="utf-8") as f:
            assert f.read() == content
        snapshot(result)
    else:
        # Pokud je outside, použij přímo
        rel_path = file_path if file_path.startswith("..") else os.path.relpath((test_dir / file_path), sandbox_dir)
        with pytest.raises(FileSystemError) as excinfo:
            write_tool._run(file_path=rel_path, content=content)
        assert isinstance(excinfo.value.__cause__, expected_exception)
        snapshot(str(excinfo.value))




# --- ReadFileTool Tests ---
@pytest.mark.parametrize("file_path,content,should_succeed,expected_exception", [
    ("test_read.txt", "Read me!", True, None),
    ("../outside_read.txt", "fail", False, PathOutsideSandboxError),
])
def test_read_file(request, sandbox_snapshot, file_path, content, should_succeed, expected_exception, snapshot):
    write_tool, read_tool, _, test_dir_name, test_dir, sandbox_dir = sandbox_snapshot
    if should_succeed:
        rel_path = os.path.relpath((test_dir / file_path), sandbox_dir)
        write_tool._run(file_path=rel_path, content=content)
        result = read_tool._run(file_path=rel_path)
        assert content in result
        snapshot(result)
    else:
        rel_path = file_path if file_path.startswith("..") else os.path.relpath((test_dir / file_path), sandbox_dir)
        with pytest.raises(FileSystemError) as excinfo:
            read_tool._run(file_path=rel_path)
        assert isinstance(excinfo.value.__cause__, expected_exception)
        snapshot(str(excinfo.value))
@pytest.mark.parametrize("file_path,content,should_succeed,expected_exception,desc", [
    ("test_read.txt", "Readable content.", True, None, "valid file"),
    ("non_existent.txt", None, False, FileSystemNotFoundError, "not found"),
    (".", None, False, IsDirectoryError, "is directory"),
    ("../../AGENTS.md", None, False, PathOutsideSandboxError, "outside sandbox"),
])
def test_read_file_param(request, sandbox_snapshot, file_path, content, should_succeed, expected_exception, desc, snapshot):
    write_tool, read_tool, _, test_dir_name, test_dir, sandbox_dir = sandbox_snapshot
    rel_path = file_path if file_path.startswith("..") else os.path.relpath((test_dir / file_path), sandbox_dir)
    if should_succeed:
        write_tool._run(file_path=rel_path, content=content)
        result = read_tool._run(file_path=rel_path)
        assert result == content
        snapshot(result)
    else:
        # Pokud testujeme "is directory", vytvoř adresář
        if desc == "is directory":
            (test_dir / file_path).mkdir(parents=True, exist_ok=True)
        with pytest.raises(FileSystemError) as excinfo:
            read_tool._run(file_path=rel_path)
        assert isinstance(excinfo.value.__cause__, expected_exception)
        snapshot(str(excinfo.value))



# --- ListDirectoryTool Tests ---
@pytest.mark.parametrize("setup_files, path, should_succeed, expected_exception, desc, expected_result", [
    (["file1.txt", "subdir/file2.txt"], ".", True, None, "dir with files", ["file1.txt", "subdir/"]),
    ([], ".", True, None, "empty dir", []),
    ([], "non_existent_dir", False, FileSystemNotFoundError, "not found", None),
    (["test_file.txt"], "test_file.txt", False, NotDirectoryError, "is file", None),
    ([], "../", False, PathOutsideSandboxError, "outside sandbox", None),
])
def test_list_directory_param(request, sandbox_snapshot, setup_files, path, should_succeed, expected_exception, desc, expected_result, snapshot):
    write_tool, _, list_tool, test_dir_name, test_dir, sandbox_dir = sandbox_snapshot
    # Vytvoř potřebné soubory/adresáře v test_dir
    for f in setup_files:
        full_path = test_dir / f
        dir_path = full_path.parent
        dir_path.mkdir(parents=True, exist_ok=True)
        rel_file_path = os.path.relpath(full_path, sandbox_dir)
        write_tool._run(file_path=rel_file_path, content="test")
    rel_path = path if path.startswith("..") else os.path.relpath((test_dir / path), sandbox_dir)
    if should_succeed:
        result = list_tool._run(path=rel_path)
        assert sorted(result) == sorted(expected_result)
        snapshot(result)
    else:
        with pytest.raises(FileSystemError) as excinfo:
            list_tool._run(path=rel_path)
        assert isinstance(excinfo.value.__cause__, expected_exception)
        snapshot(str(excinfo.value))



# --- Async Tests ---


@pytest.mark.asyncio
@pytest.mark.parametrize("file_path,content,should_succeed,expected_exception", [
    ("test_fs_data/async_read.txt", "Async readable content.", True, None),
    ("test_fs_data/non_existent_async.txt", None, False, FileSystemNotFoundError),
])
async def test_arun_read_file(request, sandbox_snapshot, file_path, content, should_succeed, expected_exception, snapshot):
    write_tool, read_tool, _, test_dir_name, test_dir, sandbox_dir = sandbox_snapshot
    if should_succeed:
        write_tool._run(file_path=file_path, content=content)
        result = await read_tool._arun(file_path=file_path)
        assert result == content
        snapshot(result)
    else:
        with pytest.raises(FileSystemError) as excinfo:
            await read_tool._arun(file_path=file_path)
        assert isinstance(excinfo.value.__cause__, expected_exception)
        snapshot(str(excinfo.value))

@pytest.mark.asyncio
@pytest.mark.parametrize("setup_files, path, should_succeed, expected_exception, expected_result", [
    (["async_file.txt"], "test_fs_data", True, None, ["async_file.txt"]),
    ([], "test_fs_data/non_existent_dir", False, FileSystemNotFoundError, None),
])
async def test_arun_list_directory(request, sandbox_snapshot, setup_files, path, should_succeed, expected_exception, expected_result, snapshot):
    write_tool, _, list_tool, test_dir_name, test_dir, sandbox_dir = sandbox_snapshot
    for f in setup_files:
        full_path = os.path.join(test_dir_name, f)
        dir_path = os.path.dirname(full_path)
        if dir_path and not os.path.exists(os.path.join(sandbox_dir, dir_path)):
            os.makedirs(os.path.join(sandbox_dir, dir_path), exist_ok=True)
        write_tool._run(file_path=full_path, content="test")
    if should_succeed:
        result = await list_tool._arun(path=path)
        assert sorted(result) == sorted(expected_result)
        snapshot(result)
    else:
        with pytest.raises(FileSystemError) as excinfo:
            await list_tool._arun(path=path)
        assert isinstance(excinfo.value.__cause__, expected_exception)
        snapshot(str(excinfo.value))

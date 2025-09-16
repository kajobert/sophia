import pytest
from tools.file_system import WriteFileTool, ReadFileTool, ListDirectoryTool

def test_write_file_tool():
    tool = WriteFileTool()
    assert hasattr(tool, 'run_sync')
    assert hasattr(tool, '__call__')

def test_read_file_tool():
    tool = ReadFileTool()
    assert hasattr(tool, 'run_sync')
    assert hasattr(tool, '__call__')

def test_list_directory_tool():
    tool = ListDirectoryTool()
    assert hasattr(tool, 'run_sync')
    assert hasattr(tool, '__call__')

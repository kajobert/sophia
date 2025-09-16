import pytest
from tools.memory_tools import MemoryReaderTool

def test_memory_reader_tool_init():
    tool = MemoryReaderTool()
    assert hasattr(tool, 'run_sync')
    assert hasattr(tool, 'run_async')
    assert hasattr(tool, '__call__')

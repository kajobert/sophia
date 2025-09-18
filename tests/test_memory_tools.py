import pytest
from tools.memory_tools import MemoryReaderTool

def test_memory_reader_tool_init():
    tool = MemoryReaderTool()
    assert hasattr(tool, '_run')
    assert hasattr(tool, '_arun')
    assert hasattr(tool, '__call__')

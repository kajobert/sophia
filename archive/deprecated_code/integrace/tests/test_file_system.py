from tools.file_system import WriteFileTool, ReadFileTool, ListDirectoryTool


def test_write_file_tool():
    tool = WriteFileTool()
    assert hasattr(tool, "_run")
    assert hasattr(tool, "_arun")


def test_read_file_tool():
    tool = ReadFileTool()
    assert hasattr(tool, "_run")
    assert hasattr(tool, "_arun")


def test_list_directory_tool():
    tool = ListDirectoryTool()
    assert hasattr(tool, "_run")
    assert hasattr(tool, "_arun")

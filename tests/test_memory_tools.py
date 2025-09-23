from tools.memory_tools import MemoryReaderTool


def test_memory_reader_tool_init():
    tool = MemoryReaderTool()
    assert hasattr(tool, "_run")
    assert hasattr(tool, "_arun")
        assert hasattr(tool, "run")
    
    def test_memory_reader_tool_run():
        tool = MemoryReaderTool()
        # Replace 'expected_output' and 'input_data' with appropriate values for your tool
        input_data = "test input"
        expected_output = "expected output"
        output = tool.run(input_data)
        assert output == expected_output

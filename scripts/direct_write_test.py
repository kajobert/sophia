# scripts/direct_write_test.py
import logging
from pathlib import Path
from plugins.tool_file_system import FileSystemTool

class DummyContext:
    def __init__(self):
        self.logger = logging.getLogger("direct_write_test")


def main():
    repo_root = Path(__file__).resolve().parents[1]
    sandbox = repo_root / "sandbox"
    tool = FileSystemTool()
    tool.setup({"sandbox_dir": str(sandbox)})
    ctx = DummyContext()
    filename = "direct_test_by_agent.txt"
    msg = tool.write_file(ctx, filename, "OK from direct test\n")
    print("write_file returned:", msg)
    abs_path = (sandbox / filename).resolve()
    print("Expected file path:", abs_path)

if __name__ == '__main__':
    main()

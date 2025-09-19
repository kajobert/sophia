import unittest
from tools.system_awareness import SystemAwarenessTool

class TestSystemAwarenessTool(unittest.TestCase):
    def test_run(self):
        """Test that the tool runs and returns the expected string."""
        tool = SystemAwarenessTool()
        result = tool._run()
        self.assertIn("Current working directory is:", result)

if __name__ == '__main__':
    unittest.main()

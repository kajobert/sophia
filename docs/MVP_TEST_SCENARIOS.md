# MVP Test Scenarios for the Proactive Agent

This document outlines test scenarios for the new proactive agent architecture (MVP).

## Scenario 1: Proactive File Creation

This scenario tests the agent's ability to recover from a simple error and proactively change its plan.

**Mission Goal:** "Read the contents of the file named `proactive_test.txt` and then delete it."

**Expected Agent Behavior:**

1.  **Thinking:** The agent will likely decide the first logical step is to read the file. It will generate a tool call for `read_file("proactive_test.txt")`.
2.  **Executing Tool (Fail):** The `read_file` tool will fail because the file does not exist. The orchestrator will catch the `FileNotFoundError`.
3.  **Handling Error:** The agent will re-enter the `THINKING` state (specifically, the `HANDLING_ERROR` path). The history will now contain the error from the failed tool call.
4.  **Proactive Re-planning:** The agent, seeing the `FileNotFoundError`, should understand that it cannot read a file that doesn't exist. It should decide that the best corrective action is to *create* the file first. It will generate a tool call for `create_file_with_block("proactive_test.txt", "This is a test.")`.
5.  **Executing Tool (Success):** The `create_file_with_block` tool will succeed.
6.  **Thinking:** The agent will now re-evaluate the mission. The file exists. It should now decide to `read_file("proactive_test.txt")` again.
7.  **Executing Tool (Success):** The `read_file` tool will succeed and return the content.
8.  **Thinking:** The agent sees that the first part of the mission is complete. It will now decide to `delete_file("proactive_test.txt")`.
9.  **Executing Tool (Success):** The `delete_file` tool will succeed.
10. **Thinking:** The agent will analyze the history and determine that all parts of the mission goal have been met. It will call `mission_complete()`.
11. **Mission Complete:** The orchestrator will terminate the mission successfully.

**Verification:**

*   The agent should not ask for user help.
*   The final state of the mission should be `MISSION_COMPLETE`.
*   The `proactive_test.txt` file should not exist in the sandbox at the end of the mission.
*   The agent's history log should clearly show the failed `read_file` attempt, followed by the successful `create_file_with_block`, `read_file`, and `delete_file` calls.
def show_last_output() -> str:
    """
    Displays the last full, unabbreviated output from a tool.
    Useful when the previous tool's output was too long and was summarized.
    """
    # The actual logic for this is handled by the orchestrator,
    # as it's the component that holds the state (the last full output).
    # This function serves as a signal for the orchestrator to perform the action.
    return "Displaying last full output."
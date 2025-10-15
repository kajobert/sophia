def task_complete(reason: str) -> str:
    """
    Call this function when the user's request has been fully and successfully completed.
    Provide a brief summary of how the task was completed in the 'reason' argument.
    """
    return f"Task marked as complete. Reason: {reason}"
# Jules's Project-Specific Instructions

This file contains important, project-specific conventions and instructions for Jules to follow.

## Code Formatting

### Handling Long Lines

To resolve line-length conflicts between `black` and `ruff` for long lines that cannot be broken (like log messages or complex assertions), use the following pattern:

1.  Wrap the line with `# fmt: off` and `# fmt: on` directives.
2.  Add a `# noqa: E501` comment to the end of the long line itself.

**Example:**

```python
# fmt: off
logger.info("This is a very long log message that exceeds the 99-character line limit and cannot be easily broken up.")  # noqa: E501
# fmt: on
```

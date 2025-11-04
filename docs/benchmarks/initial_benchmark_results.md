# Initial LLM Benchmark Results

This document summarizes the results of the initial benchmark conducted to test the tool-use and planning capabilities of various low-cost Large Language Models (LLMs).

## Test Scenario

The test involved a single, consistent task for each model:

**Task:** "list all plugins and write them to a file named 'plugins.txt'"

This task requires the model to:
1.  Understand the user's intent.
2.  Formulate a two-step plan involving the `list_plugins` and `write_file` tools.
3.  Correctly format the tool calls in a way the Kernel can parse.
4.  Utilize the output of the first step as input for the second step.

## Benchmark Summary

The following table details the performance of each tested model. All models were selected based on their low cost (under $0.10 per million tokens) and their declared support for tool use.

| Model                                          | Status  | Reason for Failure                                 |
| ---------------------------------------------- | ------- | -------------------------------------------------- |
| `mistralai/mistral-7b-instruct-v0.3`             | SUCCESS | -                                                  |
| `meta-llama/llama-3.1-8b-instruct`               | SUCCESS | -                                                  |
| `google/gemma-2-9b-it`                           | FAILURE | Endpoint does not support tool use.                |
| `qwen/qwen-2.5-7b-instruct`                      | FAILURE | Generated malformed JSON for the tool call.        |
| `microsoft/phi-3.5-mini-128k-instruct`           | FAILURE | Provider endpoint requires non-standard configuration. |

## Conclusion

The benchmark successfully identified two highly capable and cost-effective models:
*   **`mistralai/mistral-7b-instruct-v0.3`**
*   **`meta-llama/llama-3.1-8b-instruct`**

These models can serve as excellent low-cost options for routine planning and tool execution tasks within the Sophia V2 architecture. The failures also provided valuable insights into the inconsistencies of tool-use support across different models and providers, which will inform future improvements to the Kernel's robustness.

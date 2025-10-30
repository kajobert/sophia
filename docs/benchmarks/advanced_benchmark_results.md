# Advanced LLM Benchmark Results

This document summarizes the results of the advanced, multi-step benchmark.

## Test Scenario

The task was: "List all available plugins, write the list to a temporary file named `plugins.tmp`, read that file, reformat its content into a Markdown table using an LLM, and finally, write the resulting Markdown to a new file named `plugins.md`."

Each model was tested three times to ensure consistency.

## Benchmark Results

| Model                                    | Run 1   | Run 2 | Run 3 | Notes                                     |
| ---------------------------------------- | ------- | ----- | ----- | ----------------------------------------- |
| `mistralai/mistral-7b-instruct-v0.3`     | FAILURE | FAILURE | FAILURE | Consistently hallucinated a non-existent `llm_chain` tool. |
| `meta-llama/llama-3.1-8b-instruct`       | FAILURE | FAILURE | FAILURE | Consistently returned a truncated, incomplete JSON plan.     |

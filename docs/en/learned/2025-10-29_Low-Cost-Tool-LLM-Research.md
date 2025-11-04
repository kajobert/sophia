# Findings: Low-Cost Tool-Capable LLMs on OpenRouter

**Date:** 2025-10-29
**Author:** Jules v1.2

## 1. Objective

This document captures the findings from a brief research initiative to identify the most cost-effective Large Language Models (LLMs) on OpenRouter that support tool calling (function calling). The goal was to find suitable candidates for a benchmark to test the Sophia V2 system's capabilities with less expensive models.

While the benchmark itself was superseded by a higher-priority mission, the research data remains valuable for future cost-optimization efforts.

## 2. Research Process

The research was conducted by consulting the OpenRouter documentation and using targeted Google searches. The primary method was to find and filter OpenRouter's model list by price and the "tools" supported parameter.

## 3. Identified Candidates

The following models were identified as the most promising low-cost candidates that support tool calling. Prices are per million tokens (Input/Output) and are subject to change.

| Model Name                               | Price (Input/Output per M tokens) | Key Characteristics                               |
| ---------------------------------------- | --------------------------------- | ------------------------------------------------- |
| **`mistralai/mistral-7b-instruct`**      | $0.028 / $0.054                   | High-performing 7B parameter model. Industry standard. |
| **`google/gemma-2-9b-it`**               | $0.07 / $0.14                     | Google's next-gen open model.                       |
| **`qwen/qwen-2.5-7b-instruct`**          | $0.10 / $0.10                     | Strong multilingual and instruction-following model. |
| **`microsoft/phi-3.5-mini-128k-instruct`** | $0.25 / $1.25                     | Very capable small model with a large context window. |

## 4. Key Takeaway: The `litellm` Provider Prefix

During an initial aborted benchmark test with `mistralai/mistral-7b-instruct`, a critical technical detail was discovered:

*   The `litellm` library, which Sophia V2 uses to interface with LLMs, requires a provider prefix for non-OpenAI models accessed through OpenRouter.
*   **Incorrect format:** `mistralai/mistral-7b-instruct`
*   **Correct format:** `openrouter/mistralai/mistral-7b-instruct`

Failure to include the `openrouter/` prefix results in a `litellm.BadRequestError`. This is a crucial piece of information for any future work involving a variety of models.

This finding was preserved even though the full benchmark was not completed, and it will inform future model integration efforts.

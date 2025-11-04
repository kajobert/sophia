# IDEAS

## Architecture: Strategic Model Orchestrator

**Vision:**
To give Sophia the ability to dynamically and intelligently select the best LLM model for a given task, optimizing for both cost and performance. This moves beyond a static model choice towards a self-optimizing system.

**Technical procedure:**

1.  **Model Strategy Configuration:** Create a `config/model_strategy.yaml` file that defines which models to use for different types of tasks (e.g., simple summarization, code analysis, creative writing).
2.  **Cognitive Task Router:** Implement a new cognitive plugin (`cognitive_task_router.py`) that runs before the `CognitivePlanner`. Its sole responsibility is to classify the user's request into a task type and select the appropriate model from the strategy configuration.
3.  **Self-Optimization Loop (During "Sleep"):**
    *   Sophia will periodically analyze data from the `Model Evaluator` benchmark database.
    *   Her goal will be to identify more optimal models (better price/performance) for specific task types.
    *   Based on this analysis, she will be able to propose and automatically update the `config/model_strategy.yaml` file, thus improving her own efficiency over time.
4.  **Feedback Integration:** The system will log failed LLM responses. During self-optimization, Sophia will analyze these failures to identify underperforming models for certain tasks and adjust the strategy accordingly.

---

## Tool: Model Evaluator

**Vision:**
To create a systematic, data-driven way to benchmark and evaluate LLM models available via OpenRouter. This tool will provide the objective data needed for the `Strategic Model Orchestrator` to make intelligent decisions.

**Technical procedure:**

1.  **Implement `tool_model_evaluator.py`:** A new tool plugin with methods for evaluating models.
2.  **`evaluate_model` Function:** This core function will:
    *   Accept a `model_name`, `prompt`, and `evaluation_criteria`.
    *   **Measure Performance:** Record response time, token usage, and calculate the exact cost using OpenRouter's API.
    *   **Evaluate Quality:** Use a powerful "judge" model (e.g., Claude 3 Opus) to score the test model's response against the given criteria on a scale of 1-10.
    *   **Return Structured JSON:** Output a detailed JSON object containing all performance metrics and quality scores, ready for storage and analysis.
3.  **Benchmark Suite:** The tool will be used to run comprehensive benchmarks (like our 8-step test) across a range of models, creating a rich database of results in `docs/benchmarks/`.

**Initial Implementation Roadmap:**

1.  **Phase 1: Tool Implementation & Data Gathering:**
    *   Implement the `tool_model_evaluator.py` plugin as specified above.
    *   Create a helper script to query the OpenRouter API for a list of all available models and their pricing.
2.  **Phase 2: Initial Benchmark Execution:**
    *   **Model Selection:**
        *   Select the **20 most promising models** with a price under **$0.50 / 1M tokens**.
        *   Select **3 high-performance reference models** with a price under **$2.00 / 1M tokens**.
    *   **Execution:** Run the standard 8-step project benchmark on all selected models.
    *   **Budget Control:** The total cost for this initial benchmark must not exceed **$3.00**. Cost estimates must be performed after the first few runs to ensure compliance.
3.  **Phase 3: Analysis and Reporting:**
    *   Process the structured JSON outputs from the benchmark.
    *   Create a summary report in `docs/benchmarks/` with leaderboards for models in different price categories ($0.1, $0.2, $0.3, $0.4, $0.5), focusing on the price/performance ratio.

---

## Robust Tool-Calling using "Validation & Repair Loop" instead of Finetuning

**Problem:**
We need the AI agent (Sophia) to call tools using JSON with 100% reliability. Finetuning models is expensive, time-consuming, and never guarantees 100% success.

**Solution: "Validation & Repair Loop"**
Instead of trying to force the model to never make a mistake, we will actively assume that it will make a mistake, and we will have a process to fix it immediately.

**Platform:**
Use OpenRouter to access the best models in terms of price/performance (e.g., Claude 3 Haiku, Mixtral, Llama 3 70B) instead of paying a premium for expensive models (Gemini Pro, GPT-4o).

**Technical procedure (Python):**

1.  **Schema Definition:** Use the **Pydantic** library to define the exact data structure (schema) of the JSON we expect from the AI for the tool call.
2.  **First attempt (Try):** We ask a cheap model (e.g., Claude 3 Haiku) to generate the JSON for the tool call.
3.  **Validation (Except):** We immediately try to parse the model's response using our Pydantic schema in a `try...except` block.
4.  **Repair Loop:**
    * If `ValidationError` fails (`except ValidationError as e:`):
    * We take the original broken JSON *and* the detailed error message from Pydantic (`e.errors()`).
    * We send both back to the same (or another cheap) model.
    * Prompt for repair: `"ATTENTION: The JSON failed validation. Errors: [insert e.errors() here]. Fix the JSON. Do not apologize, just send the corrected code."`
5.  **Result:** This process is cheaper (uses cheap models) and much more robust (it catches and fixes errors that a more expensive, fine-tuned model would make). The goal is not 100% model success, but 99.9%+ success of the entire system.

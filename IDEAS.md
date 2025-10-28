# IDEAS

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

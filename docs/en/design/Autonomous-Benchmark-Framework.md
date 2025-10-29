# Design Document: Autonomous Benchmark Framework (ABF)

**Author:** Jules v1.2
**Date:** 2025-10-29
**Status:** DRAFT

## 1. Vision & Goal

The "benchmark debugging" process has proven to be an invaluable tool for identifying and fixing deep architectural flaws in the Sophia V2 system. However, the process is currently manual, requiring an operator to define a complex prompt, observe the failure, and manually analyze logs to diagnose the root cause.

The goal of the **Autonomous Benchmark Framework (ABF)** is to automate this entire process. The ABF will be a suite of tools and plugins that allow us to define, execute, and analyze complex benchmark scenarios programmatically. This will provide a consistent, repeatable, and efficient way to stress-test the system's capabilities, catch regressions, and accelerate the development of a robust AGI.

## 2. Core Components

The ABF will consist of three main components:

### 2.1. Benchmark Scenario Definition Files

Instead of ad-hoc prompts, we will create a library of structured benchmark scenarios defined in YAML files. This allows for version control, consistency, and easy extension.

*   **Location:** `benchmarks/scenarios/`
*   **Format:** YAML
*   **Structure:**
    ```yaml
    # benchmarks/scenarios/file_io_and_summarization.yaml
    name: "File I/O with LLM Summarization"
    description: "Tests the agent's ability to perform file I/O, chain results, and use the LLM tool for a language task."
    author: "Jules v1.2"

    prompt: >
      List all available plugins, write the list to a temporary file named 'temp_plugins.txt',
      read the content of this file, then use an LLM to reformat the content into a
      Markdown table, and finally, write the resulting Markdown to a new file named 'plugins.md'.

    assertions:
      - type: "plan_succeeded"
        description: "The overall plan must execute without critical errors."
      - type: "file_exists"
        path: "sandbox/plugins.md"
        description: "The final output file must be created."
      - type: "file_contains"
        path: "sandbox/plugins.md"
        content: "| Plugin Type | Plugin Name |"
        description: "The output file must contain the Markdown table header."
      - type: "log_contains"
        level: "INFO"
        message: "Plan executed successfully."
        description: "The final log message should indicate success."
    ```

### 2.2. The `BenchmarkRunner` Plugin

This will be a new `CORE` type plugin responsible for discovering, executing, and evaluating the benchmark scenarios.

*   **File:** `plugins/core_benchmark_runner.py`
*   **Type:** `CORE`
*   **Key Methods:**
    *   `list_benchmarks()`: Discovers all YAML files in the `benchmarks/scenarios/` directory.
    *   `run_benchmark(name: str)`: Executes a specific benchmark by name.
    *   `run_all_benchmarks()`: Executes all discovered benchmarks.
*   **Execution Flow:**
    1.  The `run_benchmark` method will read the specified YAML file.
    2.  It will create a new, isolated instance of the Kernel for the test run. This is crucial to prevent state leakage between tests.
    3.  It will pass the `prompt` from the scenario file to the Kernel's `consciousness_loop` using the non-interactive `--test` mode mechanism.
    4.  It will capture all logs, the final result, and the state of the sandbox filesystem after the run.
    5.  It will then iterate through the `assertions` in the scenario file, evaluating each one against the captured results.

### 2.3. The `BenchmarkResultReporter`

This component will be responsible for formatting and presenting the results of a benchmark run.

*   **Implementation:** Initially, this can be a simple class within the `BenchmarkRunner` plugin.
*   **Functionality:**
    *   It will take the list of evaluated assertions from a benchmark run.
    *   It will generate a clear, concise report indicating the overall status (PASS/FAIL) and the result of each individual assertion.
    *   **On Failure:** If an assertion fails, the report will include detailed diagnostic information, such as:
        *   The full log output for the session.
        *   The final state of the `SharedContext`.
        *   A snapshot of the relevant files in the sandbox.
*   **Output:** The report will be printed to the console and saved to a timestamped file in a `benchmarks/results/` directory.

## 3. Integration with the Development Workflow

The ABF will be integrated into our standard development and CI/CD processes.

*   **Local Development:** A developer can easily run a specific benchmark from the command line to test their changes: `python run.py --run-benchmark "File I/O with LLM Summarization"`
*   **Continuous Integration (CI):** Our CI pipeline will be configured to run all benchmarks automatically on every commit to the `develop` branch. This will act as a powerful regression testing suite, ensuring that no change breaks core functionality.

## 4. Future Enhancements

*   **Model Benchmarking:** The scenario definition could be extended to allow specifying different LLM models to run the same prompt against, allowing for automated model capability testing.
*   **Performance Metrics:** The `BenchmarkRunner` could capture and report performance metrics, such as the time taken for each step and the total execution time.
*   **Interactive Debugging:** A more advanced version could allow "replaying" a failed benchmark run, pausing at each step to allow a developer to inspect the state of the system.

This design provides a clear roadmap for building a powerful, automated framework that will be essential for the long-term stability and advancement of the Sophia V2 project.

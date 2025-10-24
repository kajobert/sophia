# Document 4: Development Guidelines

These guidelines are mandatory for all development to ensure code quality, consistency, and maintainability.

## 1. Coding Style & Quality

*   **PEP 8:** All Python code must adhere to the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide.
*   **Formatting:** We use `black` for automated code formatting. All code must be formatted before committing.
*   **Linting:** We use `ruff` to catch common errors and style issues. Code must be free of linting errors.

## 2. Type Annotations

*   **100% Type Hinted:** All functions, methods, and variables must have explicit type annotations in accordance with [PEP 484](https://www.python.org/dev/peps/pep-0484/).
*   **Static Analysis:** We use `mypy` to enforce type correctness. Your code must pass `mypy` checks without errors.

## 3. Docstrings and Comments

*   **Google Style Docstrings:** All modules, classes, functions, and methods must have comprehensive docstrings following the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
*   **Clarity Over Cuteness:** Write clear, concise comments where the code's purpose is not immediately obvious. Avoid unnecessary or distracting comments.

## 4. Language and Localization

*   **English Only:** All code, including comments, docstrings, variable names, and log messages, **must be written in English**.
*   **Rationale:** This is a universal standard in software development that ensures the project is accessible to the widest possible audience of developers and contributors.
*   **Documentation:** User-facing documentation can be bilingual, residing in the `docs/en/` and `docs/cs/` directories.

## 5. Configuration and Secrets Management

To ensure security, centralization, and ease of management, the following rule applies:

**Plugins must never manage their own configuration or read configuration files/environment variables directly.**

*   **Dependency Injection Principle:**
    1.  All configuration (API keys, paths, feature flags) is defined **only** in a central configuration file (e.g., `config/settings.yaml`).
    2.  The **`PluginManager`** is the sole component responsible for reading this configuration.
    3.  During plugin initialization (within its `setup()` method), the `PluginManager` will pass all the necessary configuration values that the specific plugin requires.
    4.  Therefore, the plugin receives its settings "from the outside" and never concerns itself with where they came from.

*   **Advantages:**
    *   **Security:** API keys and other sensitive data are centralized, not scattered throughout the plugin codebase.
    *   **Centralization:** When a parameter needs to be changed, it is done in a single location.
    *   **Testability:** During testing, we can easily inject a mock configuration into a plugin without needing to manipulate files or environment variables.

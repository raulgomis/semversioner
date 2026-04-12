# Semversioner - AI Agent Guidelines

This document provides a comprehensive overview of the `semversioner` project to help AI agents (and human developers) understand the architecture, coding standards, and development workflows when contributing to the codebase.

## 1. Project Overview

`semversioner` is a Python CLI tool designed to simplify semantic versioning and changelog generation. It automates the semver release process for projects, utilizing a specific directory structure (`.semversioner/`) to track changes over time and aggregate them into single versioned releases.

The tool uses a workflow where individual "changesets" are created during development (e.g., `patch`, `minor`, `major`) and stored as JSON files. During a release, these changesets are merged into a single release JSON file, and a changelog can be generated from these release records using Jinja2 templates.

## 2. Tech Stack & Dependencies

* **Language:** Python >= 3.10
* **CLI Framework:** `click`
* **Templating:** `jinja2` (for changelog generation)
* **Versioning parsing:** `packaging`
* **Build System:** `setuptools` (`pyproject.toml` based)
* **Linting & Formatting:** `ruff`
* **Testing:** `pytest`, `pytest-cov`

## 3. Architecture & Core Components

The codebase is structured to separate concerns between the CLI interface, the business logic, storage, and data models:

* **`semversioner/cli.py`**: The entry point for the CLI commands (e.g., `add-change`, `release`, `changelog`, `status`, `next-version`, `current-version`, `check`). It parses user inputs using `click` and delegates execution to the core layer.
* **`semversioner/core.py`**: The main business logic layer containing the `Semversioner` orchestrator class. It coordinates actions between the CLI and the storage layer, handles version incrementing logic, and formats the changelog using Jinja2 templates.
* **`semversioner/models.py`**: Data representations using Python `dataclasses` (e.g., `Changeset`, `Release`, `ReleaseStatus`).
* **`semversioner/storage.py`**: Handles file system interactions. Uses an abstract `SemversionerStorage` class with a concrete `SemversionerFileSystemStorage` implementation. It creates JSON changesets in the `.semversioner/next-release/` directory and aggregates them into versioned JSON files in `.semversioner/`.

## 4. Key Concepts

* **Changeset:** A single change (patch, minor, or major) representing a feature or fix. Stored as an individual JSON file in `.semversioner/next-release/`.
* **Release:** An aggregated record of all changesets for a specific version. When `semversioner release` is run, all changesets in the `next-release` folder are combined into `<version>.json` (e.g., `1.0.0.json`) and the `next-release` contents are cleared.
* **Backward Compatibility:** The storage layer includes legacy support to detect if an old `.changes/` directory is used instead of the modern `.semversioner/` directory.

## 5. Development Workflows & Commands

The project includes a `Makefile` that simplifies common tasks. **Always utilize these `make` targets during development.**

* **Setup Environment:** `make setup`
  Creates a virtual environment (`venv`), upgrades `pip`, and installs the package with its development dependencies (`pip install -e .[dev]`).
* **Linting & Formatting:** `make lint`
  Runs `ruff check .` for linting and `ruff format --check .` for code formatting checks. Ensure your code passes these checks before finalizing changes.
* **Testing:** `make test`
  Runs the test suite using `pytest`.
* **Coverage:** `make coverage`
  Runs tests and generates a terminal coverage report.
* **Clean:** `make clean`
  Removes the virtual environment, build artifacts, cache directories (`__pycache__`, `.pytest_cache`, `.ruff_cache`), and coverage files.

## 6. Coding Standards & Best Practices

1. **Type Hints:** Use strict Python type annotations everywhere (methods, variables, etc.).
2. **Dataclasses:** Prefer `dataclasses` over standard classes for simple data structures, as seen in `models.py`. Note that custom JSON encoders (`EnhancedJSONEncoder`) are used to properly serialize dataclasses in the storage layer.
3. **Error Handling:** Use custom exceptions inheriting from `SemversionerError` (e.g., `MissingChangesetError`).
4. **Testing:** Write pure `pytest` tests. The project was recently migrated from `unittest` to pure `pytest` conventions. Use fixtures instead of standard `setUp`/`tearDown` methods.
5. **Linting Context:** Be mindful of the `.ruff_cache` and `pyproject.toml` configurations. Lines are limited to 120 characters. Unnecessary `# noqa` comments or type suppression should be avoided in favor of writing idiomatic, properly typed code.

## 7. AI Agent Guidelines

* **Read Before Modifying:** When tasked with a feature or bug fix, always inspect the `core.py` and `storage.py` files to ensure new logic aligns with the file system lifecycle of changesets.
* **Verification:** Do not consider a task complete without running `make test` and `make lint`. Ensure you add appropriate tests if you introduce a new feature or fix a bug.
* **Imports:** Use absolute imports (e.g., `from semversioner.models import Release`) rather than relative imports.
* **Idempotency:** When interacting with the file system (e.g., within `storage.py`), ensure operations gracefully handle existing states (like file-already-exists errors), as seen in the retry loop inside `SemversionerFileSystemStorage.create_changeset`.

# Python Utils

[![Tests](https://github.com/justinmstuart/python-utils/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/justinmstuart/python-utils/actions/workflows/tests.yml)

This is a collection of Python scripts to automate tasks.

## Available Scripts

Scripts are fully tested, linted, and compatible with both direct execution and Python's module runner (-m).

- **scripts/trim_filenames.py**: Recursively removes a specified number of characters from the beginning of filenames in a directory and its subdirectories.
- **scripts/mp3_metadata_stripper.py**: Recursively removes metadata from mp3 and m4a files in a directory and its subdirectories.
- **scripts/cbz_processor.py**: Compresses and optimizes CBZ files in a directory (see script for details).

## Requirements

- Python 3.12+

## Getting Started

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Scripts

You can run any script directly or as a module:

```bash
python -m scripts.trim_filenames
python -m scripts.mp3_metadata_stripper
python -m scripts.cbz_processor
```

## Linting & Code Quality

To check code quality and style (using your project's .pylintrc):

```bash
pylint --rcfile=.pylintrc scripts tests
```

## Running Tests

To run all tests:

```bash
pytest
```

## Running Tests with Coverage

To run all tests and check code coverage:

```bash
coverage run -m pytest && coverage report --include=scripts/*
```

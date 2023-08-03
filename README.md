# Summarise Code Files <!-- omit from toc -->
- [Setup](#setup)
- [User Guide](#user-guide)
- [Changelog](#changelog)

This Python utility uses AI LLMs to summarise code files, producing a short summary of the important aspects for each file.

## Setup

This tool has been developed as a Python CLI (command-line interface), so to use first install, then run commands via the terminal.

We will install the tool in a local virtual environment, using venv.

To create our virtual environment and install the tool, run the following commands 
from the project directory:
 - Windows:
```powershell
python -m venv ./venv  # Create the virtual environment in the current directory
.\venv\Scripts\activate  # Activate the virtual environment
pip install .  # Install the codesummariser Python package
```
 - Linux:
```bash
python -m venv ./venv  # Create the virtual environment in the current directory
source ./venv/bin/activate  # Activate the virtual environment
pip install .  # Install the codesummariserrfmon Python package
```

To create the environment used to develop the tools, use:
```bash
pip install -r requirements-dev.txt
```

## User Guide

Once you are in an activated environment (see [setup](#setup)), you can run the 
tool using
```bash
codesummariser
```
To get help on the available options, use
```bash
codesummariser --help
```

The output of this is also included below:
```
> codesummariser --help
usage: codesummariser [-h] [--search-dirs SEARCH_DIRS [SEARCH_DIRS ...]] [--code-exts CODE_EXTS [CODE_EXTS ...]]
                      [--summary-store SUMMARY_STORE] [--model MODEL] [--max-tokens MAX_TOKENS] [--model-temperature MODEL_TEMPERATURE]       
                      [--cost-per-1k-tokens COST_PER_1K_TOKENS] [--always-check-existing-summaries] [--recursive]

options:
  -h, --help            show this help message and exit
  --search-dirs SEARCH_DIRS [SEARCH_DIRS ...]
                        Which directories to search for code files. Can be multiple, will default to:
                        [WindowsPath('C:/Users/michael.walshe/source/katalyze-data/code-summariser/data/inputs')]
  --code-exts CODE_EXTS [CODE_EXTS ...]
                        Which code extensions to search for. Can be multiple, will default to: {'.sas'}
  --summary-store SUMMARY_STORE
                        Where to store the code summary CSV, defaults to C:\Users\michael.walshe\source\katalyze-data\code-
                        summariser\data\summaries\summary.csv
  --model MODEL         Which OpenAI model to use, defaults to: gpt-3.5-turbo
  --max-tokens MAX_TOKENS
                        Max tokens to pass to the LLM in one chunk, defaults to: 4096
  --model-temperature MODEL_TEMPERATURE
                        How deterministic is the model?
  --cost-per-1k-tokens COST_PER_1K_TOKENS
                        How much does the model cost?
  --always-check-existing-summaries
                        codesummariser will check if there is an existing CSV in the summary-store location. If this flag is set, it will     
                        error if that store does not exist.
  --recursive           Whether to search --search-dirs recursively
```

## Changelog
All notable changes to this project will be documented in here. This project 
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### Unreleased <!-- omit from toc -->

 - No unreleased changes yet

### 1.0.0 - 2023-03-24 <!-- omit from toc -->

Initial solution release.

#### Added <!-- omit from toc -->
- All Features
#### Changed <!-- omit from toc -->
- n/a
#### Removed <!-- omit from toc -->
- n/a
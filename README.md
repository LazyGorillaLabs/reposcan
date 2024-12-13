# RepoScan

## Overview

RepoScan is a tool designed to help end-users assess and report on the presence of suspicious or malicious code within open-source repositories before they run it locally. While open source code can be inspected by anyone, in practice it’s rarely done thoroughly due to complexity, time constraints, and lack of expertise. RepoScan aims to bridge this gap by automating basic security checks and eventually offering more advanced capabilities such as AST-based analysis, vulnerability checking, and optional AI-driven summaries.

**What problem does RepoScan solve?**  
In today’s open-source ecosystem, users frequently download and run code from GitHub, PyPI, npm, or other sources without fully understanding what the code might be doing behind the scenes. Malicious actors can slip in backdoors, data exfiltration, or other unethical behaviors quite easily. RepoScan provides a basic first line of defense by scanning code repositories and highlighting suspicious patterns. It doesn’t guarantee absolute safety, but it helps users make more informed decisions.

## Current Status

**What RepoScan Does Today:**

- **Basic Pattern-Based Scanning:**  
  RepoScan currently scans Python, JavaScript, and related file types for simple suspicious patterns. These include occurrences of `eval()`, `exec()`, suspicious imports, and hardcoded URLs.  
- **Local and Remote Repos:**  
  It can clone a repository from a given GitHub URL or run checks directly on local directories.
- **Report Generation:**  
  Results are compiled into a human-readable Markdown report. Suspicious files and patterns are listed, giving the user a quick overview of potential concerns.
- **Logging:**  
  The tool uses Python’s `logging` module to record its actions, making it easier to trace issues and understand the scanning process.

At this stage, RepoScan is an MVP (Minimum Viable Product): a basic but functional tool that lays the groundwork for more advanced features.

## Architecture & Code Structure

The project is structured to allow easy expansion and modularity. Key directories and their purposes:

- **`src/main.py`**: The entry point for the application’s CLI usage. It orchestrates cloning/fetching the repository, scanning files, and generating reports.
- **`src/utils/`**:  
  - `repo_handler.py`: Handles cloning, verifying local paths, and gathering target files for scanning.  
  - `report_generator.py`: Formats and produces the final Markdown report.  
  - `config.py`: Stores global configuration variables (e.g., file extensions to scan).  
  - `logger.py`: Sets up the logging environment.
- **`src/patterns/`**: Holds the regex-based suspicious patterns, separated by language in future expansions. Currently includes `common_patterns.py` for patterns shared across Python/JS.
- **`src/scanners/`**:  
  - `pattern_scanner.py`: The initial scanner that matches suspicious patterns in files.  
  - Future scanners will be added here, such as `ast_scanner.py` for AST-based analysis or `dependency_checker.py`.
- **`src/llm/`**:  
  Reserved for future integration of Large Language Models (LLMs) to interpret code and produce advanced summaries.
- **`tests/`**:  
  Placeholder directory for unit tests to ensure code quality and maintainability.

This modular structure allows developers and the community to add new features, patterns, and scanning strategies without disrupting the existing codebase.

## Usage

**Prerequisites:**

- Python 3.7+ (Recommended)
- `git` installed if you plan to scan remote repositories.

**Installation (Local Development):**

```bash
cd project_root
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # If a requirements file is present, else skip
Running the Tool:

To scan a remote GitHub repo:

bash
cd project_root
python -m src.main https://github.com/someuser/somerepo
To scan a local directory:

bash
cd project_root
python -m src.main /path/to/local/repo
The tool will print out a Markdown-formatted report to stdout.

Roadmap & Planned Features
Short-Term:

Improve Pattern Scanning:
Add more language-specific patterns and refine regex matches to reduce false positives.
Logging Improvements:
Fine-tune log levels and add more contextual logging to aid debugging.
Dependency Checker:
Integrate a tool to identify if the repo depends on known-vulnerable or malicious packages (e.g., via CVE databases).
Medium-Term:

AST-Based Analysis:
Implement AST scanners for Python and JavaScript to detect more subtle malicious behaviors (like dynamic code execution or suspicious control flows).
LLM Integration (Optional):
Use a Large Language Model for deeper insights:
File-by-File Analysis: Ask the LLM to summarize suspicious logic found by the pattern-based and AST scanners.
Final Report Summaries: Provide a natural language summary of the entire repository’s risk profile for non-technical users.
Long-Term:

Sandboxed Dynamic Analysis:
Safely execute the code in a controlled environment to observe runtime behavior.
Multi-Language Support:
Expand beyond Python/JS to cover languages like Go, Rust, or C/C++.
Community-Driven Rule Sets:
Allow users to contribute their own suspicious pattern rules and share them, making RepoScan a community-driven project.
Contributing
The project is still in its early stages. Community feedback, code contributions, and suggestions for patterns and scanning techniques are welcome. By contributing, you help make open-source software safer and more transparent for everyone.

License
MIT

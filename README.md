# RepoScan

## Overview

RepoScan is a tool designed to help end-users assess and report on the presence of suspicious or malicious code within open-source repositories before they run it locally. While open source code can be inspected by anyone, in practice it’s rarely done thoroughly due to complexity, time constraints, and lack of expertise. RepoScan aims to bridge this gap by automating basic security checks and eventually offering more advanced capabilities such as AST-based analysis, vulnerability checking, and optional AI-driven summaries.

**What problem does RepoScan solve?**  
In today’s open-source ecosystem, users frequently download and run code from GitHub, PyPI, npm, or other sources without fully understanding what the code might be doing behind the scenes. Malicious actors can slip in backdoors, data exfiltration, or other unethical behaviors quite easily. RepoScan aims to provide a basic first line of defense by scanning code repositories and highlighting suspicious patterns. It does not and can not guarantee absolute safety, but merely aims to help users who are security consious make more informed decisions about where to direct their attention. 

**Existing Tools**
I'm not a security expert. I want to utilize existing security tools and libraries wherever possible, and convert their output to something at least directionally useful for other non-experts.

## Current Status

**What RepoScan Does Today:**

- **Basic Pattern-Based Scanning:**  
  RepoScan currently scans Python, JavaScript, and related file types for simple suspicious patterns. These include occurrences of `eval()`, `exec()`, suspicious imports, and hardcoded URLs. These can direct limited attention to higher risk areas of code. 
- **Local and Remote Repos:**  
  It can clone a repository from a given GitHub URL, pypi package, npm package, a remote file, or run checks directly on local directories.
- **Dependency Checks:**
  Runs pip-audit or npm-audit on found dependency manifests to report known vulnerabilities. 
- **Report Generation:**  
  Results are compiled into a human-readable Markdown report. Suspicious files and patterns are listed, giving the user a quick overview of potential concerns.
- **Logging:**  
  The tool uses Python’s `logging` module to record its actions, making it easier to trace issues and understand the scanning process.

At this stage, RepoScan is an MVP (Minimum Viable Product): a basic but functional tool that lays the groundwork for more advanced features.


## Usage

**Prerequisites:**

- Python 3.7+ (Recommended)
- `git` installed for remote repositories
- `npm` installed for JavaScript scanning (optional)
- `pip-audit` for Python dependency checking
- `eslint` for JavaScript analysis (optional)

**Installation (Local Development):**

```bash
cd project_root
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
npm install -g eslint  # Optional, for JavaScript scanning
```

**Running the Tool:**

Basic usage with all scanners enabled:
```bash
python -m src.main <input>
```

Disable specific scanners:
```bash
python -m src.main <input> --no-ast --no-eslint
```

Input can be:
- GitHub: `https://github.com/user/repo` or `github:user/repo`
- PyPI: `pypi:packagename`
- NPM: `npm:packagename`
- Remote: `https://example.com/file.py`
- Local: `/path/to/local/repo` or `/path/to/file.py`

The tool generates a detailed Markdown report including:
- Dependency vulnerability analysis
- Suspicious code patterns
- AST-based findings
- ESLint warnings (if enabled)

## Roadmap & Planned Features

**Short-Term:**

- Replace current scanners with more robust existing open source solutions
- Refactor scanners -> plugins for said external tools
- Logging Improvements: Save log files by default instead of littering stdout.
- Improved reporting details about exactly what is suspicious, what ip is being called, what is exec() ing, etc for static checks
- --output -o flag to output to a file, or reponame_scan_Timestamp.md by default
- Debug mode for full tracing --debug -d
- Lots of testing and example collecting

**Medium-Term:**

- Integrate as many additional existing security analysis tools as possible as plugins
- Improve Telemetry analysis to determine what infomation is being gathered and shared with whom
- LLM Integration (Optional):
Use a Large Language Model for deeper insights:
  - File-by-File Analysis: Ask the LLM to summarize suspicious logic found by the pattern-based and AST scanners, or all files if desired. 
  - Final Report Summaries: Provide a natural language summary of the entire repository’s risk profile for non-technical users.

**Long-Term:**

- Better help/documentation --help -h is something that should exist.   
- Multi-Language Support:
Expand beyond Python/JS to cover languages like Go, Rust, or C/C++.
- Community-Driven Expansion
Allow users to contribute their own plugins and share them, making RepoScan a community-driven project.
- If LLM/AI mode enabled, option to enter chat with repo vulnerabilities mode to ask questions about findings (use custom sys instructions and preloaded context plus report)

## Contributing
The project is still in its early stages. Community feedback, code contributions, and suggestions for patterns and scanning techniques are welcome. By contributing, you help make open-source software safer and more transparent for everyone.

## License
MIT

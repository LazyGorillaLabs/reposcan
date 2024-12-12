There seems to be a gap in the open source ecosystem. Code execution is always risky, but the promise of open source is that you can review all the code yourself to ensure it's safe and to modify it to meet your needs. In current practice however, few people review even a significant fraction of the code that they download and execute on their local machines and in the cloud. It would be difficult to manually review everything even if one were so inclined, as years of projects building upon one another leads quickly to an explosion of lines of code if one wants to be thorough. Plenty of static analysis and even more advanced tools exist to help devs write secure, bug free code. But there's not currently anything I'm aware of that's targeted to end users who want to scan github repos, pip packages, and other source code they didn't write themselves to ensure it's not intentionally malicious. For example, currently an individual, criminal organization, or state actor could fork a highly popular viral repo (say, the latest automatic1111 for example, but anything really) and write themselves in a backdoor, keylogger, or just send all your work off to themselves and with some positive media attention (real or paid) they could easily compromise lots of systems from people looking to harness open source to help with their problems. Or, slightly less maliciously, a genuinely useful package may be sending a copy of all your prompts/data to a central server for logging, which may be fine if disclosed, but end users may have no way of knowing otherwise. The vision of this project is to provide a basic line of defense against these deliberately malicious (or non-disclosing) repos. Nothing we do can ensure that code is safe to run, but we can do some basic sanity checks to filter out the most obvious and egregious offences. 

There are a variety of approaches we could take to do something like this. The simplest is probably a traditional script. We could just process each and every file in a repo independently in a series of passes looking for things like http requests, urls, telemetry calls, allowing external connections, backdoors, known security flaws, whatever, adding passes for each as we discover them. We could add options to check known databases for dependencies, or an option to scan them ourselves some day. Eventually maybe even some sandboxed code execution to get more hidden behavior, but let's leave that for later for now. I'd like to focus on simple, useful, and working before moving to complex. After the loop over everything we could output some form of report to the user showing what we found. An alternative approach might be passing each file to a highly capable large context window LLM asking it to evaluate the file. Even this might benefit from being broken up into several passes, each prompted with instructions to look out for a particular type of threat. A third approach might be to combine the above two approaches, using code to highlight relvant files and bring them to the LLM for further analysis. Yet another option is to create examples and train up an LLM powered AI agent enabled with appropriate tools so the LLM can explore on it's own. I think a final optional LLM step might be useful at the final reporting stage even if we use traditional code only through the rest of the process, just to summarize and draw attention to important findings. 

Here's the overall roadmap we're currently pursuing:


Phase 1: MVP (Static Only)

Repo Cloning & File Gathering:
Implement a function that given a GitHub URL, clones (or downloads) the repo into a temporary directory.
Basic Keyword & Regex Scans:
Implement a config file with known suspicious patterns (like suspicious domain list, known malicious function calls).
Scan every file, record hits.
Dependency Checks:
For Python, parse requirements.txt or pyproject.toml.
For Node/JS, parse package.json.
Call a vulnerability API or have a local database of known malicious packages.
Initial Report Generation:
Combine the scan results into a simple Markdown or text report.


Phase 2: Improved Static Analysis & AST

Implement AST parsing for Python & JS:
Use Python’s ast module and a JS parser (like acorn or esprima) to look for suspicious constructs.
Add rules to detect dynamic code execution, outbound network calls, credential usage, and environment variable manipulation at the AST level.
Integrate a scoring system: give each suspicious pattern a weight and produce a risk score.


Phase 3: Optional LLM Step

Add a command-line flag or config option --use-llm to enable LLM analysis.
Implement a pipeline where flagged files are extracted and sent to an LLM API (e.g., via OpenAI API or a local model endpoint).
Prompt the LLM to summarize and highlight suspicious logic.
Include the LLM output in the final report. Make it clear this step is heuristic and optional.


Phase 4: User Experience & Packaging

Create a simple CLI tool that can be installed via pip install my-scan-tool.
Possibly build a small web frontend (Flask, FastAPI + a static page) so users can paste a repo URL in their browser.
Add documentation, a README, and usage examples.


Phase 5: Community Engagement & Expansion

Invite community submissions of suspicious pattern rules.
Add support for more languages as requested by the community.
Consider integrating sandboxed dynamic analysis as a premium or advanced feature.

Phase 6: Expand 

More Features, Supported languages, Advanced analysis features (sandboxing, Agentic analysis, etc)
eg) scan a pypi url / pip package name
- paranoid mode : scan every file regardless of type with all scans, including full llm scans if enabled, and all optional and future scans.
- webui
- virtualization detection detection / sandboxed execution prevention detection / debugger detection detection
- Train a full on dspy or other llm agent on examples and have it run full time
- integrate external knowledgebases / vulnerability tools/ known vulnerability lookups
- more advanced dependency analysis



Proposed project structure ideas:
project_root/
│ readme.md
│ scan.py                      #convenience entry point calling main.py
├─ src/
│  ├─ main.py                  # Main entry point and orchestration logic
│  │
│  ├─ scanners/                # Modules related to scanning & analysis
│  │  ├─ __init__.py
│  │  ├─ base_scanner.py       # Abstract classes or interfaces for scanners
│  │  ├─ pattern_scanner.py    # Current regex-based pattern scanner
│  │  ├─ ast_scanner.py        # Future AST-based analysis (Python/JS)
│  │  ├─ dependency_checker.py  # Future: checks dependencies for known vulnerabilities
│  │  └─ (other specialized scanners as needed)
│  │
│  ├─ patterns/                # Language-specific and common suspicious patterns
│  │  ├─ __init__.py
│  │  ├─ common_patterns.py    # Patterns common to multiple languages (URLs, eval, etc.)
│  │  ├─ python_patterns.py    # Python-specific suspicious patterns
│  │  ├─ javascript_patterns.py# JS-specific suspicious patterns
│  │  └─ (additional languages as needed)
│  │
│  ├─ llm/                     # LLM integration modules
│  │  ├─ __init__.py
│  │  ├─ llm_analyzer.py       # Sends code/context to LLM, gets back analysis
│  │  ├─ llm_summary.py        # Uses LLM to produce a final summary of findings
│  │  └─ prompts/              # Prompt templates for LLM usage
│  │     ├─ summary_prompt.txt
│  │     └─ analysis_prompt.txt
│  │
│  ├─ utils/                   # General utilities, helpers, and configuration
│  │  ├─ __init__.py
│  │  ├─ repo_handler.py       # Cloning/fetching repos, handling local paths
│  │  ├─ report_generator.py   # Functions to produce final markdown/HTML reports
│  │  ├─ config.py             # Central place for config constants (e.g., file extensions)
│  │  └─ logger.py             # Optional: Logging utilities
│  │
│  └─ __init__.py
│
└─ tests/                      # Unit tests for each module (future)
   ├─ test_pattern_scanner.py
   ├─ test_repo_handler.py
   ├─ test_llm_analyzer.py
   └─ ...


   Key Points of this Structure:

src/main.py acts as the main orchestration point. It uses utility functions to clone or load the repo and then invokes various scanners. After scanning, it calls the report generator (and optionally the LLM modules) to produce the final output.
scanners/ directory groups all scanning logic. Each scanner can focus on one approach (pattern-based, AST-based, dependency checks). They can share interfaces or inherit from a base_scanner.py.
patterns/ directory holds the suspicious patterns organized by language. The common_patterns.py might contain regexes or checks that are language-agnostic, while python_patterns.py and javascript_patterns.py focus on language-specific markers.
llm/ directory encapsulates all LLM-related functionality, making it optional. If the user has an API key or a local model, they can enable it. If not, the tool still runs using just the scanners.
utils/ directory holds reusable utilities (like repo handling, configuration, and reporting tools).

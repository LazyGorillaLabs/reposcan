# project_root/src/patterns/common_patterns.py
"""
Common suspicious patterns used across languages.
For now, just the initial set of regexes from our first draft.
Later we can split by language if needed.
"""

import re

SUSPICIOUS_PATTERNS = {
    "http_url": re.compile(r"https?://[^\s'\"]+"),
    "eval_call": re.compile(r"\beval\s*\("),
    "exec_call": re.compile(r"\bexec\s*\("),
    "suspicious_import": re.compile(r"(importlib\.import_module|__import__|import )"),
    # Add more patterns as needed...
}


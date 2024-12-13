# project_root/src/patterns/python_patterns.py
"""
Python-specific suspicious patterns.

Focus on imports and calls known for enabling malicious behaviors:
- smtplib, socket for networking/email
- pynput, keyboard for potential keylogging
- subprocess for external command execution
- requests for outbound HTTP calls (not always malicious, but let's flag it)
"""

import re

PYTHON_SUSPICIOUS_PATTERNS = {
    "py_import_smtplib": re.compile(r"\bimport\s+smtplib\b"),
    "py_import_socket": re.compile(r"\bimport\s+socket\b"),
    "py_import_pynput": re.compile(r"\bimport\s+pynput\b"),
    "py_import_keyboard": re.compile(r"\bimport\s+keyboard\b"),
    "py_import_subprocess": re.compile(r"\bimport\s+subprocess\b"),
    "py_subprocess_call": re.compile(r"subprocess\.(run|Popen|check_output)\("),
    "py_import_requests": re.compile(r"\bimport\s+requests\b"),
    # Already have eval/exec in common patterns, but we could add more python-specific if needed.
}


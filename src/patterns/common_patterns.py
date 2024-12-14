# project_root/src/patterns/common_patterns.py
"""
Common suspicious patterns that apply across multiple languages.

These are broad and may produce false positives, but serve as a first step
in identifying potentially malicious or suspicious content.
"""

import re

SUSPICIOUS_PATTERNS = {
    # Existing patterns from before
    "http_url": re.compile(r"https?://[^\s'\"]+"),
    "eval_call": re.compile(r"\beval\s*\("),
    "exec_call": re.compile(r"\bexec\s*\("),
    "code_import": re.compile(r"(importlib\.import_module|__import__|import )"),
    
    # New Common Patterns
    # 1. IP addresses (IPv4 only, naive)
    "ip_address": re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
    
    # 2. Email addresses
    # Matches common email pattern, not perfect but good enough for a heuristic scan
    "email_address": re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),
    
    # 3. Keylogging keyword (very naive)
    "keylogger_keyword": re.compile(r"\bkeylog(ger)?\b"),
    
    # 4. VM/Sandbox/Debugger Indicators (naive keyword matches)
    # This will likely catch even references in comments or docstrings.
    "vm_related_terms": re.compile(r"\b(virtualbox|vmware|sandbox|qemu|debugger)\b"),
}

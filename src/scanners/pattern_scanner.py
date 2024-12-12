# project_root/src/scanners/pattern_scanner.py
"""
A scanner that uses regex-based pattern matching to detect suspicious code.
This replicates the logic from the initial script version.
"""

import sys

# Import the patterns
from src.patterns.common_patterns import SUSPICIOUS_PATTERNS

def scan_file_for_patterns(file_path: str) -> dict:
    """
    Scan a single file for suspicious patterns. Return a dict of pattern_name->matches.
    """
    findings = {}
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            # Check each pattern
            for pattern_name, pattern_regex in SUSPICIOUS_PATTERNS.items():
                matches = pattern_regex.findall(content)
                if matches:
                    findings[pattern_name] = matches
    except Exception as e:
        # In a more robust tool, you'd handle or log this error properly.
        findings["error_reading"] = [str(e)]
    return findings


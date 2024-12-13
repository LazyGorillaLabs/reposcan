# project_root/src/scanners/pattern_scanner.py
"""
A scanner that uses regex-based pattern matching to detect suspicious code.

We now load both common patterns and language-specific patterns based on file extension.
"""

import os
from src.patterns.common_patterns import SUSPICIOUS_PATTERNS as COMMON_PATTERNS
from src.patterns.python_patterns import PYTHON_SUSPICIOUS_PATTERNS
from src.patterns.javascript_patterns import JAVASCRIPT_SUSPICIOUS_PATTERNS
from src.utils.logger import logger

def get_patterns_for_file(file_path: str) -> dict:
    """
    Determine which patterns to apply based on the file extension.
    
    - Always include common patterns.
    - If file ends with .py, also include Python-specific patterns.
    - If file ends with .js, .jsx, .ts, .tsx, include JS patterns.
    - Other languages: Just common patterns for now.
    """
    extension = os.path.splitext(file_path)[1].lower()
    patterns = COMMON_PATTERNS.copy()  # Start with common patterns
    
    if extension == ".py":
        # Merge python patterns
        patterns.update(PYTHON_SUSPICIOUS_PATTERNS)
    elif extension in [".js", ".jsx", ".ts", ".tsx"]:
        # Merge javascript patterns
        patterns.update(JAVASCRIPT_SUSPICIOUS_PATTERNS)
    
    return patterns

def scan_file_for_patterns(file_path: str) -> dict:
    findings = {}
    patterns = get_patterns_for_file(file_path)

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            for pattern_name, pattern_regex in patterns.items():
                matches = pattern_regex.findall(content)
                if matches:
                    logger.debug(f"Pattern '{pattern_name}' matched in {file_path}. {len(matches)} occurrences.")
                    findings[pattern_name] = matches
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        findings["error_reading"] = [str(e)]
    return findings

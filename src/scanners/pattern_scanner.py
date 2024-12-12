# project_root/src/scanners/pattern_scanner.py
"""
A scanner that uses regex-based pattern matching to detect suspicious code.
This replicates the logic from the initial script version.
"""

# project_root/src/scanners/pattern_scanner.py
from src.patterns.common_patterns import SUSPICIOUS_PATTERNS
from src.utils.logger import logger

def scan_file_for_patterns(file_path: str) -> dict:
    findings = {}
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            for pattern_name, pattern_regex in SUSPICIOUS_PATTERNS.items():
                matches = pattern_regex.findall(content)
                if matches:
                    logger.debug(f"Pattern '{pattern_name}' matched in {file_path}.")
                    findings[pattern_name] = matches
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        findings["error_reading"] = [str(e)]
    return findings


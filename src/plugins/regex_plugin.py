"""
Basic example to demonstrate using a plugin. Use more robust detectors for actual security checks.

"""

import os
from typing import Dict, Any
from src.patterns.common_patterns import SUSPICIOUS_PATTERNS as COMMON_PATTERNS
from src.patterns.python_patterns import PYTHON_SUSPICIOUS_PATTERNS
from src.patterns.javascript_patterns import JAVASCRIPT_SUSPICIOUS_PATTERNS
from src.plugins.base_plugin import BasePlugin 
from src.utils.logger import logger

class RegexPlugin(BasePlugin):
    """
    A scanner that uses regex-based pattern matching to detect suspicious code.

    We now load both common patterns and language-specific patterns based on file extension.
    """

    def scan(self, target_path: str) -> Dict[str, Any]:
        """
        Perform the plugin's scanning on `target_path`.
        Returns a dictionary of findings.
        """
        findings = {}
        
        # 1. If target_path is a directory, gather all the relevant files
        file_list = []
        if os.path.isdir(target_path):
            for root, dirs, files in os.walk(target_path):
                for f in files:
                    # Optional: filter by extension if desired
                    file_list.append(os.path.join(root, f))
        elif os.path.isfile(target_path):
            file_list = [target_path]
        else:
            logger.error(f"RegexPlugin: '{target_path}' is neither file nor directory?")
            return findings
        
        # 2. Now iterate over the collected files
        for file_path in file_list:
            patterns = self.get_patterns_for_file(file_path)
            if not patterns:
                continue
            
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for pattern_name, pattern_regex in patterns.items():
                        matches = pattern_regex.findall(content)
                        if matches:
                            logger.debug(f"Pattern '{pattern_name}' matched in {file_path}. {len(matches)} occurrences.")
                            findings.setdefault(file_path, {})[pattern_name] = matches
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                findings.setdefault(file_path, {})["error_reading"] = str(e)
        
        return findings

    def get_patterns_for_file(self, file_path: str) -> dict:
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

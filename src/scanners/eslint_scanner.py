# project_root/src/scanners/eslint_scanner.py
"""
ESLint-based scanner for JavaScript/TypeScript files.

This module:
- Checks if ESLint is installed.
- If installed, runs ESLint on the given JS/TS file.
- Parses the JSON output and flags any reported issues as suspicious findings.

This isn't a perfect malicious code detector, but a stepping stone
to more advanced analysis. In future, we may add custom ESLint configs
or rules for malicious detection.
"""

import subprocess
import json
from src.utils.logger import logger

def is_eslint_installed():
    """ Check if ESLint is available on the system PATH. """
    try:
        result = subprocess.run(["eslint", "--version"], capture_output=True, text=True, check=True)
        logger.debug(f"ESLint version: {result.stdout.strip()}")
        return True
    except (OSError, subprocess.CalledProcessError):
        logger.debug("ESLint not available or not working properly.")
        return False

def scan_js_file_with_eslint(file_path: str) -> dict:
    """
    Run ESLint on a single JS/TS file and parse the results.
    
    Returns a dict of findings in the same format as other scanners:
    {
      "eslint_issues": [ 
        { "line": number, "rule": "rule-id", "message": "some message" },
        ...
      ]
    }
    If no issues or eslint not installed, returns empty dict.
    """
    if not is_eslint_installed():
        logger.info("ESLint not installed, skipping ESLint scan.")
        return {}

    try:
        # Run ESLint with JSON formatter
        # --no-ignore ensures it checks even files that might be ignored by default ESLint configs
        result = subprocess.run(
            ["eslint", "--no-ignore", "--format", "json", file_path],
            capture_output=True,
            text=True
        )

        if result.returncode not in [0,1]: 
            # ESLint returns 0 if no problems, 1 if problems found
            # Any other return code might be an error
            logger.warning(f"ESLint returned an unexpected code {result.returncode}. Output: {result.stdout}")
            return {}

        # Parse JSON output
        try:
            eslint_output = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing ESLint output JSON: {e}")
            return {}

        # ESLint output is a list of results, each with .messages
        # Example structure:
        # [
        #   {
        #     "filePath": "/path/to/file.js",
        #     "messages": [
        #       {
        #         "ruleId": "no-eval",
        #         "severity": 2,
        #         "message": "eval is evil.",
        #         "line": 10,
        #         "column": 5,
        #         "nodeType": "CallExpression",
        #         "endLine": 10,
        #         "endColumn": 9
        #       }
        #     ]
        #   }
        # ]

        if not eslint_output:
            return {}

        file_result = eslint_output[0] if len(eslint_output) > 0 else None
        if not file_result or "messages" not in file_result:
            return {}

        findings = {}
        eslint_issues = []
        for msg in file_result["messages"]:
            # severity: 1=warning, 2=error
            eslint_issues.append({
                "line": msg.get("line"),
                "rule": msg.get("ruleId"),
                "message": msg.get("message"),
                "severity": "error" if msg.get("severity") == 2 else "warning"
            })

        if eslint_issues:
            findings["eslint_issues"] = eslint_issues

        return findings
    except Exception as e:
        logger.error(f"Error running ESLint on {file_path}: {e}")
        return {}


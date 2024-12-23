import os
import subprocess
import json
from src.utils.logger import logger
from typing import Dict, Any
from src.plugins.base_plugin import BasePlugin

class ESLintPlugin(BasePlugin):
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

    def scan(self, target_path: str):
        """

        Returns a dict of findings in the same format as other scanners:
        {
          "eslint_issues": [ 
            { "line": number, "rule": "rule-id", "message": "some message" },
            ...
          ]
        }

        If no issues or eslint not installed, returns empty dict.
        """
        findings = {}
        
        if not self.is_eslint_installed():
            logger.info("ESLint not installed, skipping ESLint scan.")
            return {}

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
            logger.error(f"ESLintPlugin: '{target_path}' is neither file nor directory?")
            return findings
        
        # 2. Now iterate over the collected files
        for file_path in file_list:

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
                    logger.warning(f"ESLint returned code {result.returncode}. Stdout: {result.stdout}, Stderr: {result.stderr}")
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

    def is_eslint_installed(self):
        """ Check if ESLint is available on the system PATH. """
        try:
            result = subprocess.run(["eslint", "--version"], capture_output=True, text=True, check=True)
            logger.debug(f"ESLint version: {result.stdout.strip()}")
            return True
        except (OSError, subprocess.CalledProcessError):
            logger.debug("ESLint not available or not working properly.")
            return False

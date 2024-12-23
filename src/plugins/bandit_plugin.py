import subprocess
import json
from typing import Dict, Any
from .base_plugin import BasePlugin
from src.utils.logger import logger

class BanditPlugin(BasePlugin):
    def scan(self, target_path: str) -> Dict[str, Any]:
        """
        Run Bandit against the specified directory or file, parse the results, 
        and return them in a standard dictionary format.
        """
        logger.info(f"Running Bandit plugin on: {target_path}")

        # Example: bandit requires a directory or file, plus a format specifier
        # We'll assume bandit is installed. If not, handle the error gracefully.
        result_dict = {}
        try:
            cmd = ["bandit", "-r", target_path, "-f", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode not in (0,1):
                # 0 = no issues found, 1 = issues found, other is error
                logger.error(f"Bandit returned error code: {result.returncode}")
                return result_dict

            output_json = json.loads(result.stdout)
            logger.debug(f"Bandit Output: {output_json}")

            # Convert Bandit's output to a consistent shape for your final reporting
            issues = output_json.get("results", [])
            if issues:
                result_dict["bandit_issues"] = issues

        except Exception as e:
            logger.error(f"Error running Bandit: {e}")

        return result_dict


# project_root/src/main.py
"""
Main entry point of the application.

The code uses fetch_code_source() to handle various input types:
- GitHub repositories:
  - https://github.com/user/repo
  - https://github.com/user/repo.git
  - github:user/repo
  - Single files via https://github.com/user/repo/blob/branch/path/to/file
- PyPI packages:
  - pypi:packagename
  - pip:packagename
- NPM packages:
  - npm:packagename
- Remote files:
  - http://host/file.js
  - https://host/file.py
- Local directories & files:
  - /path/to/local/dir
  - /path/to/local/file.py

The code will scan the fetched source using:
- Pattern matching builtin plugin (always enabled)
- Python AST analysis (enabled by default, disable with --no-ast)
- ESLint for JS/TS (enabled by default, disable with --no-eslint)

Usage:
  python -m src.main <input> [--no-ast] [--no-eslint]
"""

import sys
import os
import shutil
import argparse

#Utilities
from src.utils.repo_handler import fetch_code_source
from src.utils.report_generator import generate_report, get_report_filename
from src.utils.logger import logger

#Plugins to actual scanning tools
from src.plugins.regex_plugin import RegexPlugin
from src.plugins.bandit_plugin import BanditPlugin
from src.plugins.eslint_plugin import ESLintPlugin
from src.plugins.dependency_plugin import DependencyPlugin
#from src.plugins.semgrep_plugin import SemgrepPlugin

def main():
    parser = argparse.ArgumentParser(description="Scan a code source for suspicious code.")
    parser.add_argument("repo_path", help="GitHub, PyPI, NPM, remote file, local dir/file")
    parser.add_argument("--no-bandit", action="store_true", help="Disable Python Bandit scanning")
    parser.add_argument("--no-eslint", action="store_true", help="Disable ESLint scanning for JS/TS files")
    args = parser.parse_args()

    repo_input = args.repo_path
    use_bandit = not args.no_bandit
    use_eslint = not args.no_eslint

    logger.info(f"Starting scan for: {repo_input}. Bandit={use_bandit}, ESLint={use_eslint}")
    final_path = fetch_code_source(repo_input)
    logger.info(f"Code fetched at: {final_path}")

    # If final_path is a cloned GitHub repo or something fetched,
    # and we want to remove it afterward, we can keep track of that.
    # For now, let's assume we always clean up if we created a temp directory.
    # We'll only cleanup if we detect a temporary directory created by fetch functions:
    cleanup_needed = final_path.startswith("/tmp/repo_scan_") or "repo_scan_" in final_path

    try:

        # Initialize plugins
        plugins = [
            RegexPlugin(),
            BanditPlugin(),
            ESLintPlugin(),
            DependencyPlugin(),
            # SemgrepPlugin(), ...
        ]
        
        scan_results = {}
        for plugin in plugins:
            logger.info(f"Running plugin: {plugin.name}")
            # We're defining the convention that plugins get the directory name and choose for themselves which files to process
            plugin_result = plugin.scan(final_path)
            scan_results[plugin.name] = plugin_result


        # Generate and save report
        report = generate_report(scan_results)
        output_dir = "reports"
        report_filename = get_report_filename(repo_input)
        report_path = os.path.join(output_dir, report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Report saved to: {report_path}")
    finally:
        # Clean up if we fetched code into a temp directory.
        # This logic might need more robust detection in real usage.
        # For now, just check if final_path is a temporary directory.
        if cleanup_needed and not os.path.isfile(final_path):
            logger.debug(f"Removing temporary directory: {final_path}")
            shutil.rmtree(final_path, ignore_errors=True)

    logger.info("Scan complete.")


if __name__ == "__main__":
    main()

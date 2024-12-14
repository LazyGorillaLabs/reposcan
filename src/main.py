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
- NPM packages:
  - npm:packagename
- Remote files:
  - http://host/file.js
  - https://host/file.py
- Local directories & files:
  - /path/to/local/dir
  - /path/to/local/file.py

The code will scan the fetched source using:
- Pattern matching (always enabled)
- Python AST analysis (enabled by default, disable with --no-ast)
- ESLint for JS/TS (enabled by default, disable with --no-eslint)

Usage:
  python -m src.main <input> [--no-ast] [--no-eslint]
"""

import sys
import os
import shutil
import argparse

from src.utils.repo_handler import fetch_code_source, gather_files
from src.scanners.pattern_scanner import scan_file_for_patterns
from src.scanners.ast_scanner import scan_python_file_with_ast
from src.scanners.eslint_scanner import scan_js_file_with_eslint
from src.utils.report_generator import generate_report
from src.utils.logger import logger

def main():
    parser = argparse.ArgumentParser(description="Scan a code source for suspicious code.")
    parser.add_argument("repo_path", help="GitHub, PyPI, NPM, remote file, local dir/file")
    parser.add_argument("--no-ast", action="store_true", help="Disable Python AST scanning")
    parser.add_argument("--no-eslint", action="store_true", help="Disable ESLint scanning for JS/TS files")
    args = parser.parse_args()

    repo_input = args.repo_path
    use_ast = not args.no_ast
    use_eslint = not args.no_eslint

    logger.info(f"Starting scan for: {repo_input}. AST={use_ast}, ESLint={use_eslint}")
    final_path = fetch_code_source(repo_input)
    logger.info(f"Code fetched at: {final_path}")

    # If final_path is a cloned GitHub repo or something fetched,
    # and we want to remove it afterward, we can keep track of that.
    # For now, let's assume we always clean up if we created a temp directory.
    # We'll only cleanup if we detect a temporary directory created by fetch functions:
    cleanup_needed = final_path.startswith("/tmp/repo_scan_") or "repo_scan_" in final_path

    try:
        files_to_scan = gather_files(final_path)
        logger.info(f"Found {len(files_to_scan)} files to scan.")

        scan_results = {}
        for fpath in files_to_scan:
            logger.debug(f"Scanning file: {fpath}")
            # Regex-based scan
            result = scan_file_for_patterns(fpath)

            # Python AST scan if enabled
            if use_ast and fpath.endswith(".py"):
                ast_result = scan_python_file_with_ast(fpath)
                for k, v in ast_result.items():
                    result.setdefault(k, []).extend(v)

            # ESLint scan if enabled and file is JS/TS
            if use_eslint and any(fpath.endswith(ext) for ext in [".js", ".jsx", ".ts", ".tsx"]):
                eslint_result = scan_js_file_with_eslint(fpath)
                for k, v in eslint_result.items():
                    result.setdefault(k, []).extend(v)

            if result:
                scan_results[fpath] = result

        report = generate_report(scan_results)
        print(report)
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

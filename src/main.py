# project_root/src/main.py
"""
Main entry point of the application.

Now the code uses fetch_code_source() to handle various input types:
- GitHub (github:user/repo or https://github.com/user/repo) - working
- PyPI (pypi:packagename) - not yet implemented, will error
- NPM (npm:packagename) - not yet implemented, will error
- Remote file (http://host/file.js) - not yet implemented, will error
- Local directory or file - working

Then it scans the resulting directory/file.

Usage:
  python -m src.main <input> [--use-ast] [--use-eslint]
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
    parser.add_argument("--use-ast", action="store_true", help="Enable Python AST scanning")
    parser.add_argument("--use-eslint", action="store_true", help="Enable ESLint scanning for JS/TS files")
    args = parser.parse_args()

    repo_input = args.repo_path
    use_ast = args.use_ast
    use_eslint = args.use_eslint

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

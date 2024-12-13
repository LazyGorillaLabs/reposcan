# project_root/src/main.py
"""
Main entry point of the application.

This file orchestrates:
- Taking user input for a repo (URL or local path)
- Cloning/validating repo via repo_handler
- Gathering files
- Running pattern scans
- Generating and displaying a report

Later steps will integrate other scanners, LLM analysis, etc.
"""

import sys
import shutil
import argparse

from src.utils.repo_handler import clone_repo_if_needed, gather_files
from src.scanners.pattern_scanner import scan_file_for_patterns
from src.scanners.ast_scanner import scan_python_file_with_ast
from src.scanners.eslint_scanner import scan_js_file_with_eslint
from src.utils.report_generator import generate_report
from src.utils.logger import logger


def main():
    parser = argparse.ArgumentParser(description="Scan a repository for suspicious code.")
    parser.add_argument("repo_path", help="URL or local path to the repository")
    parser.add_argument("--use-ast", action="store_true", help="Enable Python AST scanning")
    parser.add_argument("--use-eslint", action="store_true", help="Enable ESLint scanning for JS/TS files")
    args = parser.parse_args()

    repo_input = args.repo_path
    use_ast = args.use_ast
    use_eslint = args.use_eslint

    logger.info(f"Starting scan for repository: {repo_input}, AST scanning = {use_ast}, ESLint = {use_eslint}")
    repo_path = clone_repo_if_needed(repo_input)
    logger.info(f"Repository prepared at: {repo_path}")

    try:
        files_to_scan = gather_files(repo_path)
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
                    # Merge results just like with AST
                    result.setdefault(k, []).extend(v)

            if result:
                scan_results[fpath] = result

        report = generate_report(scan_results)
        print(report)
    finally:
        if repo_input.startswith("http"):
            logger.debug("Removing cloned temporary repository.")
            shutil.rmtree(repo_path, ignore_errors=True)

    logger.info("Scan complete.")

if __name__ == "__main__":
    main()


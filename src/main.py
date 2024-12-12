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

from src.utils.repo_handler import clone_repo_if_needed, gather_files
from src.scanners.pattern_scanner import scan_file_for_patterns
from src.utils.report_generator import generate_report
from src.utils.logger import logger

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.main <repo_url_or_local_path>")
        sys.exit(1)

    repo_input = sys.argv[1]
    logger.info(f"Starting scan for repository: {repo_input}")

    repo_path = clone_repo_if_needed(repo_input)
    logger.info(f"Repository prepared at: {repo_path}")

    try:
        files_to_scan = gather_files(repo_path)
        logger.info(f"Found {len(files_to_scan)} files to scan.")

        scan_results = {}
        for fpath in files_to_scan:
            logger.debug(f"Scanning file: {fpath}")
            result = scan_file_for_patterns(fpath)
            if result:
                scan_results[fpath] = result

        report = generate_report(scan_results)
        # Print the report to stdout for now
        print(report)
    finally:
        # If we cloned a temp repo, clean it up
        if repo_input.startswith("http"):
            logger.info("Removing cloned temporary repository.")
            shutil.rmtree(repo_path, ignore_errors=True)

    logger.info("Scan complete.")
    

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A first draft of a malicious code scanning tool. 

This version is a basic implementation focusing on:
- Cloning or downloading a GitHub repository (if a URL is provided).
- Running simple static pattern checks on files.
- Generating a summary report of suspicious findings.

This code is meant as an initial baseline, aligning with the roadmap discussed:
Phase 1: MVP (Static Only)
 - Clone repo
 - Basic keyword/regex scans
 - Simple report

Future work will involve:
 - More advanced AST checks
 - Dependency vulnerability checks
 - Optional LLM integration
 - Improved UI/UX

Note:
 - In a real scenario, error handling, logging, and UI would be more robust.
 - Security considerations (like carefully handling repo URLs) should be applied.
 - This example uses subprocess for git clone and rudimentary regex matching.
 - The suspicious patterns are just examples and not exhaustive.

Usage:
  python scan.py <repo_url_or_local_path>

If <repo_url_or_local_path> is a GitHub URL, the script will attempt to clone it.
If it's a local directory, it will scan that directory directly.
"""

import os
import sys
import re
import tempfile
import shutil
import subprocess
from pathlib import Path

####################
# Configuration
####################

# Simple regex patterns that might indicate suspicious behavior.
# These are purely illustrative and not exhaustive.
SUSPICIOUS_PATTERNS = {
    "http_url": re.compile(r"https?://[^\s'\"]+"),
    "eval_call": re.compile(r"\beval\s*\("),
    "exec_call": re.compile(r"\bexec\s*\("),
    "suspicious_import": re.compile(r"(importlib\.import_module|__import__|import )"),
    # Add more patterns as needed...
}

# File extensions to scan in MVP. Later we can expand this.
FILE_EXTENSIONS_TO_SCAN = [".py", ".js", ".ts", ".jsx", ".tsx"]

####################
# Functions
####################

def clone_repo_if_needed(repo_url: str) -> str:
    """
    If repo_url is a Git URL (e.g., starts with http), clone it into a temp directory.
    Otherwise, assume it's a local path and return as is.
    """
    if repo_url.startswith("http"):
        tmp_dir = tempfile.mkdtemp(prefix="repo_scan_")
        # Attempt to clone the repository
        try:
            subprocess.run(["git", "clone", "--depth", "1", repo_url, tmp_dir], check=True)
            return tmp_dir
        except subprocess.CalledProcessError:
            shutil.rmtree(tmp_dir)
            print("Error: Failed to clone repository.")
            sys.exit(1)
    else:
        # Assume local directory
        if not os.path.isdir(repo_url):
            print(f"Error: The path '{repo_url}' is not a directory.")
            sys.exit(1)
        return repo_url


def gather_files(repo_path: str) -> list:
    """
    Recursively gather files from the repository path that match certain extensions.
    """
    all_files = []
    for root, dirs, files in os.walk(repo_path):
        for f in files:
            # Check file extension
            if any(f.endswith(ext) for ext in FILE_EXTENSIONS_TO_SCAN):
                all_files.append(os.path.join(root, f))
    return all_files


def scan_file_for_patterns(file_path: str) -> dict:
    """
    Scan a single file for suspicious patterns. Return a dict of pattern_name->matches.
    """
    findings = {}
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            # Check each pattern
            for pattern_name, pattern_regex in SUSPICIOUS_PATTERNS.items():
                matches = pattern_regex.findall(content)
                if matches:
                    findings[pattern_name] = matches
    except Exception as e:
        # In a more robust tool, you'd handle or log this error properly.
        # For now, just note we couldn't read this file.
        findings["error_reading"] = [str(e)]
    return findings


def generate_report(scan_results: dict) -> str:
    """
    Given the aggregated scan results, generate a simple markdown report.
    scan_results format:
      {
        "path/to/file.py": {
          "pattern_name": [list_of_matches],
          ...
        },
        ...
      }
    """
    report_lines = []
    report_lines.append("# Scan Report\n")
    suspicious_count = 0
    for file_path, patterns_found in scan_results.items():
        if patterns_found:
            suspicious_count += 1
            report_lines.append(f"## {file_path}")
            for pattern_name, matches in patterns_found.items():
                report_lines.append(f"- **{pattern_name}**: Found {len(matches)} occurrences.")
                # To avoid clutter, we won't list all matches in detail right now.
                # Future versions could show line numbers or code snippets.
            report_lines.append("")  # blank line

    if suspicious_count == 0:
        report_lines.insert(1, "No suspicious patterns found.\n")
    else:
        report_lines.insert(1, f"**Summary:** {suspicious_count} files with suspicious patterns.\n")

    return "\n".join(report_lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scan.py <repo_url_or_local_path>")
        sys.exit(1)

    repo_input = sys.argv[1]
    repo_path = clone_repo_if_needed(repo_input)
    try:
        files_to_scan = gather_files(repo_path)

        scan_results = {}
        for fpath in files_to_scan:
            result = scan_file_for_patterns(fpath)
            if result:
                scan_results[fpath] = result

        report = generate_report(scan_results)

        # Print the report to stdout for now
        # In the future, we could write to a file or a web UI.
        print(report)
    finally:
        # If we cloned a temp repo, clean it up (only if repo_input was an http URL)
        if repo_input.startswith("http"):
            shutil.rmtree(repo_path, ignore_errors=True)


if __name__ == "__main__":
    main()


# project_root/src/utils/repo_handler.py
"""
Utilities for handling repository input:
- Cloning from a Git URL if needed
- Validating local paths
- Gathering files for scanning
"""

import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path
from src.utils.config import FILE_EXTENSIONS_TO_SCAN

def clone_repo_if_needed(repo_url: str) -> str:
    """
    If repo_url is a Git URL (e.g., starts with http), clone it into a temp directory.
    Otherwise, assume it's a local path and return as is.
    """
    if repo_url.startswith("http"):
        tmp_dir = tempfile.mkdtemp(prefix="repo_scan_")
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
            if any(f.endswith(ext) for ext in FILE_EXTENSIONS_TO_SCAN):
                all_files.append(os.path.join(root, f))
    return all_files


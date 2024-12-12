# project_root/src/utils/repo_handler.py
"""
Utilities for handling repository input:
- Cloning from a Git URL if needed
- Validating local paths
- Gathering files for scanning
"""

# project_root/src/utils/repo_handler.py
import os
import sys
import tempfile
import shutil
import subprocess
from src.utils.config import FILE_EXTENSIONS_TO_SCAN
from src.utils.logger import logger

def clone_repo_if_needed(repo_url: str) -> str:
    if repo_url.startswith("http"):
        tmp_dir = tempfile.mkdtemp(prefix="repo_scan_")
        logger.info(f"Cloning repository from {repo_url} into {tmp_dir}")
        try:
            subprocess.run(["git", "clone", "--depth", "1", repo_url, tmp_dir], check=True)
            logger.debug("Clone completed successfully.")
            return tmp_dir
        except subprocess.CalledProcessError as e:
            shutil.rmtree(tmp_dir)
            logger.error(f"Error: Failed to clone repository. {e}")
            sys.exit(1)
    else:
        logger.debug(f"Using local path: {repo_url}")
        if not os.path.isdir(repo_url):
            logger.error(f"Error: The path '{repo_url}' is not a directory.")
            sys.exit(1)
        return repo_url

def gather_files(repo_path: str) -> list:
    logger.debug(f"Gathering files from {repo_path}")
    all_files = []
    for root, dirs, files in os.walk(repo_path):
        for f in files:
            if any(f.endswith(ext) for ext in FILE_EXTENSIONS_TO_SCAN):
                all_files.append(os.path.join(root, f))
    logger.debug(f"Total files matched patterns: {len(all_files)}")
    return all_files


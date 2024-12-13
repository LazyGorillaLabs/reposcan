# project_root/src/utils/repo_handler.py
"""
Utilities for handling various input sources.

Supported input formats:
1. GitHub repositories:
   - https://github.com/user/repo
   - https://github.com/user/repo.git
   - github:user/repo (short form)
   
2. PyPI packages:
   - pypi:packagename
   
3. NPM packages:
   - npm:packagename

4. Single remote file:
   - http://host/file.js
   - https://host/file.js
   (not recognized as GitHub or another known source)
   
5. Local directories & files:
   - /path/to/local/dir
   - /path/to/local/file.py

Logic:
- The main entry point is `fetch_code_source(repo_input)`.
- It checks the format of `repo_input` and calls the corresponding fetch function.
- Each fetch function returns a local path (directory or file) to be scanned.

Note:
- PyPI and NPM fetch functions are placeholders.
- fetch_remote_file() is also a placeholder that would use `requests` or `urllib` to download the file.
- For GitHub, we still clone via `git clone`.

This modular design can be extended to support more sources easily.
"""

import os
import sys
import re
import tempfile
import shutil
import subprocess
from src.utils.config import FILE_EXTENSIONS_TO_SCAN
from src.utils.logger import logger

#############################
# Helper detection functions
#############################

def is_github_input(repo_input: str) -> bool:
    """
    Detect if input is a GitHub repo reference.
    Supported forms:
    - https://github.com/user/repo(.git)
    - github:user/repo
    """
    if repo_input.startswith("https://github.com/"):
        return True
    if repo_input.startswith("github:"):
        return True
    return False

def is_pypi_input(repo_input: str) -> bool:
    """
    Detect if input is a PyPI package reference.
    Form:
    - pypi:packagename
    """
    return repo_input.startswith("pypi:")

def is_npm_input(repo_input: str) -> bool:
    """
    Detect if input is a NPM package reference.
    Form:
    - npm:packagename
    """
    return repo_input.startswith("npm:")

def is_remote_file(repo_input: str) -> bool:
    """
    Detect if input is a single remote file.
    We consider anything starting with http or https that is not github:
    Example:
    - http://example.com/file.js
    - https://example.com/file.py
    """
    if repo_input.startswith("http://") or repo_input.startswith("https://"):
        # If it's not GitHub (checked before this function is called), assume it's a remote file
        if not repo_input.startswith("https://github.com/"):
            return True
    return False

#############################
# Fetch Functions
#############################

def fetch_github_repo(repo_input: str) -> str:
    """
    Fetch a GitHub repository.
    Input could be:
    - https://github.com/user/repo
    - https://github.com/user/repo.git
    - github:user/repo

    Steps:
    1. Normalize the URL to a standard git clone URL if needed.
    2. git clone into a temp directory.
    3. Return the temp directory path.
    """
    logger.info(f"Fetching GitHub repo: {repo_input}")

    # Normalize
    if repo_input.startswith("github:"):
        # convert github:user/repo -> https://github.com/user/repo
        _, repo_path = repo_input.split("github:", 1)
        repo_url = "https://github.com/" + repo_path.strip("/")
    else:
        # Already starts with https://github.com/
        repo_url = repo_input

    tmp_dir = tempfile.mkdtemp(prefix="repo_scan_")
    try:
        subprocess.run(["git", "clone", "--depth", "1", repo_url, tmp_dir], check=True)
        logger.debug("Clone completed successfully.")
        return tmp_dir
    except subprocess.CalledProcessError as e:
        shutil.rmtree(tmp_dir)
        logger.error(f"Error: Failed to clone repository. {e}")
        sys.exit(1)

def fetch_pypi_package(package_name: str) -> str:
    """
    Fetch a PyPI package:
    Form: pypi:packagename

    For now, this is a placeholder:
    Steps might be:
    1. Use `pip download packagename -d <tmp_dir>`
    2. Extract the downloaded sdist or wheel.
    3. Return the extracted directory.

    We just log and exit for now.
    """
    logger.info(f"Fetching PyPI package: {package_name}")
    tmp_dir = tempfile.mkdtemp(prefix="repo_scan_pypi_")
    # Pseudocode (not actually implemented):
    # subprocess.run(["pip", "download", package_name, "-d", tmp_dir], check=True)
    # Extract the downloaded file (tar.gz or zip) into tmp_dir/extracted/
    # Return tmp_dir/extracted
    # For now, just return empty dir to avoid errors.
    return tmp_dir

def fetch_npm_package(package_name: str) -> str:
    """
    Fetch an NPM package:
    Form: npm:packagename

    Placeholder:
    Steps might be:
    1. `npm pack packagename` in a tmp_dir
    2. Extract the resulting tarball
    3. Return the extracted directory
    """
    logger.info(f"Fetching NPM package: {package_name}")
    tmp_dir = tempfile.mkdtemp(prefix="repo_scan_npm_")
    # Pseudocode:
    # subprocess.run(["npm", "pack", package_name], cwd=tmp_dir, check=True)
    # Find the resulting .tgz, extract it
    # return extracted directory
    return tmp_dir

def fetch_remote_file(file_url: str) -> str:
    """
    Fetch a single remote file:
    - http://host/file.js
    - https://host/file.py

    Steps:
    1. Download the file using requests or urllib
    2. Save to a temp directory
    3. Return the file path

    Placeholder for now.
    """
    logger.info(f"Fetching remote file: {file_url}")
    tmp_dir = tempfile.mkdtemp(prefix="repo_scan_file_")
    filename = os.path.basename(file_url)
    local_path = os.path.join(tmp_dir, filename)
    # Pseudocode:
    # import requests
    # r = requests.get(file_url, timeout=30)
    # with open(local_path, 'wb') as f:
    #     f.write(r.content)
    return local_path  # Just returning local_path as if downloaded.

#############################
# Main fetch entry point
#############################

def fetch_code_source(repo_input: str) -> str:
    """
    Determine the type of input and fetch the code accordingly.

    Order of checks:
    1. GitHub input?
    2. PyPI input?
    3. NPM input?
    4. Remote file input?
    5. Local file or directory?

    Return a local path (dir or file) ready for scanning.
    """
    if is_github_input(repo_input):
        return fetch_github_repo(repo_input)

    if is_pypi_input(repo_input):
        package_name = repo_input.split("pypi:", 1)[1]
        return fetch_pypi_package(package_name.strip())

    if is_npm_input(repo_input):
        package_name = repo_input.split("npm:", 1)[1]
        return fetch_npm_package(package_name.strip())

    if is_remote_file(repo_input):
        return fetch_remote_file(repo_input)

    # If none of the above, assume local path
    if os.path.isfile(repo_input) or os.path.isdir(repo_input):
        logger.debug(f"Local path detected: {repo_input}")
        return repo_input
    else:
        logger.error(f"Error: The path '{repo_input}' does not match any known format and is not local.")
        sys.exit(1)


def gather_files(repo_path: str) -> list:
    """
    If repo_path is a file, return just that file.
    If repo_path is a directory, recursively gather files matching certain extensions.
    """
    if os.path.isfile(repo_path):
        filename = os.path.basename(repo_path)
        if any(filename.endswith(ext) for ext in FILE_EXTENSIONS_TO_SCAN):
            return [repo_path]
        else:
            # Try scanning anyway since user explicitly provided it
            return [repo_path]

    # If it's a directory
    all_files = []
    for root, dirs, files in os.walk(repo_path):
        for f in files:
            if any(f.endswith(ext) for ext in FILE_EXTENSIONS_TO_SCAN):
                all_files.append(os.path.join(root, f))
    return all_files

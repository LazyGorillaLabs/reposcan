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
import tarfile
import zipfile
import requests
from pathlib import Path
from src.utils.config import FILE_EXTENSIONS_TO_SCAN
from src.utils.logger import logger

#############################
# Helper detection functions
#############################

def is_github_file_url(repo_input: str) -> bool:
    """
    Detect if input is a GitHub file URL.
    Form: https://github.com/user/repo/blob/branch/path/to/file
    """
    if repo_input.startswith("https://github.com/"):
        return "/blob/" in repo_input
    return False

def is_github_repo_url(repo_input: str) -> bool:
    """
    Detect if input is a GitHub repo reference.
    Supported forms:
    - https://github.com/user/repo(.git)
    - github:user/repo
    """
    if repo_input.startswith("https://github.com/") and not "/blob/" in repo_input:
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
    Fetch a PyPI package and extract its contents.
    Form: pypi:packagename
    
    Steps:
    1. Create temp directory
    2. Download package using pip
    3. Find and extract the downloaded archive
    4. Return path to extracted contents
    
    Returns:
        str: Path to directory containing extracted package
    """
    logger.info(f"Fetching PyPI package: {package_name}")
    
    # Create temp directory for download
    tmp_dir = tempfile.mkdtemp(prefix="repo_scan_pypi_")
    extract_dir = os.path.join(tmp_dir, "extracted")
    os.makedirs(extract_dir)
    
    try:
        # Download the package
        logger.debug(f"Downloading package {package_name}")
        subprocess.run(
            ["pip", "download", "--no-deps", package_name, "-d", tmp_dir],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Find the downloaded archive
        archives = [f for f in os.listdir(tmp_dir) 
                   if f.endswith(('.tar.gz', '.zip', '.whl'))]
        
        if not archives:
            raise FileNotFoundError(f"No package archive found for {package_name}")
            
        archive_path = os.path.join(tmp_dir, archives[0])
        
        # Extract based on archive type
        if archive_path.endswith('.tar.gz'):
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(extract_dir)
        elif archive_path.endswith(('.zip', '.whl')):  # wheels are zip files
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                
        # Find the actual package directory (usually first subdirectory)
        subdirs = [d for d in os.listdir(extract_dir) 
                  if os.path.isdir(os.path.join(extract_dir, d))]
        if subdirs:
            return os.path.join(extract_dir, subdirs[0])
        return extract_dir
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to download package {package_name}: {e.stderr}")
        shutil.rmtree(tmp_dir)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error processing package {package_name}: {str(e)}")
        shutil.rmtree(tmp_dir)
        sys.exit(1)

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

def fetch_github_file(file_url: str) -> str:
    """
    Fetch a single file from GitHub.
    Converts: 
    https://github.com/user/repo/blob/branch/path/to/file
    to:
    https://raw.githubusercontent.com/user/repo/branch/path/to/file
    """
    logger.info(f"Fetching GitHub file: {file_url}")
    
    # Convert GitHub blob URL to raw URL
    raw_url = file_url.replace("github.com", "raw.githubusercontent.com")
    raw_url = raw_url.replace("/blob/", "/")
    
    return fetch_remote_file(raw_url)

def fetch_remote_file(file_url: str) -> str:
    """
    Fetch a single remote file:
    - http://host/file.js
    - https://host/file.py

    Steps:
    1. Download the file using requests
    2. Save to a temp directory
    3. Return the file path

    Raises:
        requests.exceptions.RequestException: If download fails
    """
    logger.info(f"Fetching remote file: {file_url}")
    tmp_dir = tempfile.mkdtemp(prefix="repo_scan_file_")
    filename = os.path.basename(file_url)
    local_path = os.path.join(tmp_dir, filename)
    
    try:
        response = requests.get(file_url, timeout=30)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        with open(local_path, 'wb') as f:
            f.write(response.content)
            
        logger.debug(f"Successfully downloaded {file_url} to {local_path}")
        return local_path
        
    except requests.exceptions.RequestException as e:
        shutil.rmtree(tmp_dir)
        logger.error(f"Failed to download {file_url}: {str(e)}")
        sys.exit(1)

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
    if is_github_file_url(repo_input):
        return fetch_github_file(repo_input)
        
    if is_github_repo_url(repo_input):
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

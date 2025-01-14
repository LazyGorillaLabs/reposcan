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
   - pip:packagename (alias)
   
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
    Forms:
    - pypi:packagename
    - pip:packagename
    """
    return repo_input.startswith("pypi:") or repo_input.startswith("pip:")

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
    
    Attempts to fetch source code in this order:
    1. Try PyPI JSON API to get source distribution
    2. Try pip download with --no-binary flag
    3. Fall back to regular pip download if both above fail
    
    Returns:
        str: Path to directory containing extracted package
    """
    logger.info(f"Fetching PyPI package: {package_name}")
    
    def extract_archive(archive_path: str, extract_dir: str) -> None:
        if archive_path.endswith('.tar.gz'):
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(extract_dir)
        elif archive_path.endswith(('.zip', '.whl')):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

    def get_package_dir(extract_dir: str) -> str:
        subdirs = [d for d in os.listdir(extract_dir) 
                  if os.path.isdir(os.path.join(extract_dir, d))]
        if subdirs:
            return os.path.join(extract_dir, subdirs[0])
        return extract_dir

    tmp_dir = tempfile.mkdtemp(prefix="repo_scan_pypi_")
    extract_dir = os.path.join(tmp_dir, "extracted")
    os.makedirs(extract_dir)
    
    try:
        # First attempt: Use PyPI JSON API
        try:
            logger.debug(f"Attempting to fetch source distribution via PyPI API for {package_name}")
            pypi_url = f"https://pypi.org/pypi/{package_name}/json"
            response = requests.get(pypi_url)
            response.raise_for_status()
            package_data = response.json()
            
            # Look for source distribution
            sdist_url = None
            for url_info in package_data['urls']:
                if url_info['packagetype'] == 'sdist':
                    sdist_url = url_info['url']
                    break
                    
            if sdist_url:
                response = requests.get(sdist_url, stream=True)
                response.raise_for_status()
                
                archive_path = os.path.join(tmp_dir, os.path.basename(sdist_url))
                with open(archive_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                extract_archive(archive_path, extract_dir)
                return get_package_dir(extract_dir)
        except Exception as e:
            logger.debug(f"PyPI API attempt failed: {str(e)}")

        # Second attempt: pip download with --no-binary flag
        try:
            logger.debug(f"Attempting pip download with --no-binary flag for {package_name}")
            subprocess.run(
                ["pip", "download", "--no-deps", "--no-binary", ":all:", 
                 package_name, "-d", tmp_dir],
                check=True,
                capture_output=True,
                text=True
            )
            
            archives = [f for f in os.listdir(tmp_dir) 
                       if f.endswith(('.tar.gz', '.zip'))]
            
            if archives:
                archive_path = os.path.join(tmp_dir, archives[0])
                extract_archive(archive_path, extract_dir)
                return get_package_dir(extract_dir)
        except Exception as e:
            logger.debug(f"pip --no-binary attempt failed: {str(e)}")

        # Final attempt: regular pip download
        logger.warning(f"Falling back to regular pip download for {package_name}")
        subprocess.run(
            ["pip", "download", "--no-deps", package_name, "-d", tmp_dir],
            check=True,
            capture_output=True,
            text=True
        )
        
        archives = [f for f in os.listdir(tmp_dir) 
                   if f.endswith(('.tar.gz', '.zip', '.whl'))]
        
        if not archives:
            raise FileNotFoundError(f"No package archive found for {package_name}")
            
        archive_path = os.path.join(tmp_dir, archives[0])
        extract_archive(archive_path, extract_dir)
        return get_package_dir(extract_dir)
        
    except Exception as e:
        logger.error(f"All attempts to fetch package {package_name} failed: {str(e)}")
        shutil.rmtree(tmp_dir)
        sys.exit(1)

def is_npm_installed() -> bool:
    """Check if npm is available in the system."""
    try:
        subprocess.run(
            ["npm", "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def fetch_npm_package(package_name: str) -> str:
    """
    Fetch an NPM package:
    Form: npm:packagename
    
    Steps:
    1. Create temp directories for download and extraction
    2. Use npm pack to download the package
    3. Extract the resulting tarball
    4. Return the path to the extracted package contents
    
    Returns:
        str: Path to directory containing extracted package
    """
    logger.info(f"Fetching NPM package: {package_name}")
    
    if not is_npm_installed():
        logger.error("npm is not installed. Please install Node.js and npm first.")
        sys.exit(1)
    
    # Create temp directories
    tmp_dir = tempfile.mkdtemp(prefix="repo_scan_npm_")
    extract_dir = os.path.join(tmp_dir, "extracted")
    os.makedirs(extract_dir)
    
    try:
        # Run npm pack to download the package
        logger.debug(f"Running npm pack for {package_name}")
        result = subprocess.run(
            ["npm", "pack", package_name],
            cwd=tmp_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        # npm pack outputs the filename of the created tarball
        tarball_name = result.stdout.strip()
        tarball_path = os.path.join(tmp_dir, tarball_name)
        
        if not os.path.exists(tarball_path):
            raise FileNotFoundError(f"NPM pack did not create expected tarball: {tarball_path}")
            
        # Extract the tarball
        with tarfile.open(tarball_path, 'r:gz') as tar:
            # npm packages have a 'package' directory at root
            tar.extractall(extract_dir)
            
        # The contents will be in a 'package' directory
        package_dir = os.path.join(extract_dir, 'package')
        if not os.path.exists(package_dir):
            raise FileNotFoundError(f"Expected package directory not found in npm package")
            
        return package_dir
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to fetch npm package {package_name}: {e.stderr}")
        shutil.rmtree(tmp_dir)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error processing npm package {package_name}: {str(e)}")
        shutil.rmtree(tmp_dir)
        sys.exit(1)

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
        package_name = repo_input.split(":", 1)[1]
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

# project_root/src/scanners/dependency_checker.py
import os
import json
import tomli
import re
from pathlib import Path
"""
A module to check dependencies for known vulnerabilities or questionable packages.

Overall Goals:
- Get the dependencies for this file that is being scanned
- Identify and report known vulnerabilities using external tools or APIs.
- Return findings in a format consistent with other scanners (e.g., { "file_path": { "finding_category": [...] } })

Approach:
1. Identify Dependencies:
   - For Python: Parse requirements.txt, pyproject.toml, or setup.py to extract package names and versions.
   - For Node.js: Parse package.json and lock files.
   - For other ecosystems in the future, add more logic as needed.

2. Run Vulnerability Checks:
   - Option A: Use external tools like `pip-audit` for Python or `npm audit` for Node.js, parse their JSON output.
   - Option B: Query vulnerability APIs (like the OSV API or GitHub Advisory Database).
   - Eventually, we could combine these approaches, starting simple (external tools) and expanding as needed.

3. Don't trust the devs:
    Compare dependency manifest to actual imports to ensure consistency

4. Report Findings:
   - Produce a dictionary that maps individual dependencies to findings.
   - Integrate seamlessly with final reporting. Possibly a "dependency_concerns" key containing arrays of vulnerabilities.

Future Considerations (just keep in mind for now, noting in the code where it may go in future:
- Caching results to avoid repeatedly querying APIs 
- Allowing configuration for different vulnerability sources.
- Providing remediation suggestions or direct CVE links.

Example Workflow:
- When scanning a repo:
  1. Identify project type (Python, Node, etc.) by the code of the repo
  2. Grab a dependency manifest if available - if not, that's useful info
  3. Check repo dependency manifest for known vulnerabilities.
     If Python: run `pip-audit` over dependencies and parse results.
     If Node: run `npm audit --json` and parse results.
  4. When doing the individual files:
     Pull list of dependencies from the file
     ensure the dependency is listed in the manifest, or red-flag it
  5. Convert output into a standardized format.
  6. Return these findings to main.py, which merges them with other scanner results.

This modular design ensures we can easily add new methods or sources of vulnerability data later.
"""

def identify_file_dependencies(file_path: str) -> dict:
    """
    Identify dependencies in the given file
    Returns a language and dependency dict like:
    {
      "python": [
        "pkg_name1" ,
        "pkg_name2":
    ]}

    For now, just a placeholder:
    - In a real implementation, return the actual dependencies from the file 
    """
    return {}


def scan_file_dependencies(file_path: str, import_manifest: [str]) -> dict:
    """
    High-level function to:
    1. Identify dependencies in file.
    2. Ensure it's in the manifest
    3. Return a structured dict of findings.


    For now, returns empty results.
    """
    deps = identify_file_dependencies(file_path)
    findings = {}#build findings here
    return findings

def parse_requirements_txt(file_path: str) -> list:
    """Parse requirements.txt file and return list of (package, version) tuples"""
    deps = []
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Handle different requirement formats
                if '==' in line:
                    pkg, ver = line.split('==')
                    deps.append((pkg.strip(), ver.strip()))
                elif '>=' in line:
                    pkg, ver = line.split('>=')
                    deps.append((pkg.strip(), f">={ver.strip()}"))
                else:
                    # Package with no version specified
                    deps.append((line, ""))
    return deps

def parse_pyproject_toml(file_path: str) -> list:
    """Parse pyproject.toml and return list of (package, version) tuples"""
    deps = []
    with open(file_path, 'rb') as f:
        try:
            data = tomli.load(f)
            # Check project.dependencies
            project_deps = data.get('project', {}).get('dependencies', [])
            if project_deps:
                for dep in project_deps:
                    if ' ' in dep:
                        pkg, ver = dep.split(' ', 1)
                        deps.append((pkg.strip(), ver.strip()))
                    else:
                        deps.append((dep.strip(), ""))
            
            # Check tool.poetry.dependencies
            poetry_deps = data.get('tool', {}).get('poetry', {}).get('dependencies', {})
            if poetry_deps:
                for pkg, ver in poetry_deps.items():
                    if pkg != 'python':  # Skip python version constraint
                        deps.append((pkg, str(ver)))
        except Exception as e:
            print(f"Error parsing pyproject.toml: {e}")
    return deps

def parse_package_json(file_path: str) -> list:
    """Parse package.json and return list of (package, version) tuples"""
    deps = []
    with open(file_path) as f:
        try:
            data = json.load(f)
            # Regular dependencies
            dependencies = data.get('dependencies', {})
            deps.extend((pkg, ver) for pkg, ver in dependencies.items())
            # Dev dependencies
            dev_dependencies = data.get('devDependencies', {})
            deps.extend((pkg, ver) for pkg, ver in dev_dependencies.items())
        except Exception as e:
            print(f"Error parsing package.json: {e}")
    return deps

def identify_repo_dependencies(repo_path: str) -> dict:
    """
    Identify dependencies in the given repository path.
    Returns a dict like:
    {
      "python": {
        "requirements.txt": [(pkg_name, version), ...],
        "pyproject.toml": [(pkg_name, version), ...],
      },
      "node": {
        "package.json": [(pkg_name, version), ...],
      }
    }
    """
    result = {
        "python": {},
        "node": {}
    }
    
    repo_path = Path(repo_path)
    
    # Look for Python dependency files
    for req_file in repo_path.rglob('requirements.txt'):
        try:
            deps = parse_requirements_txt(str(req_file))
            if deps:
                rel_path = str(req_file.relative_to(repo_path))
                result["python"][rel_path] = deps
        except Exception as e:
            print(f"Error processing {req_file}: {e}")
    
    for pyproject in repo_path.rglob('pyproject.toml'):
        try:
            deps = parse_pyproject_toml(str(pyproject))
            if deps:
                rel_path = str(pyproject.relative_to(repo_path))
                result["python"][rel_path] = deps
        except Exception as e:
            print(f"Error processing {pyproject}: {e}")
    
    # Look for Node.js dependency files
    for pkg_json in repo_path.rglob('package.json'):
        try:
            deps = parse_package_json(str(pkg_json))
            if deps:
                rel_path = str(pkg_json.relative_to(repo_path))
                result["node"][rel_path] = deps
        except Exception as e:
            print(f"Error processing {pkg_json}: {e}")
    
    return result


def run_repo_vulnerability_checks(dependencies: dict) -> dict:
    """
    Given a dict of dependencies,
    run external tools or query APIs to find known vulnerabilities.

    Returns something like:
    {
      "dependency_issues": [
        {
          "package": "requests",
          "version": "2.10.0",
          "vulnerabilities": [
            {"id": "CVE-2020-1234", "description": "...", "severity": "high"},
            ...
          ]
        }
      ]
    }

    For now, just returns an empty dict.
    """
    return {}

def scan_repo_dependencies(repo_path: str) -> dict:
    """
    High-level function to:
    1. Identify dependencies in repo
    2. Run vulnerability checks on them.
    3. Return a structured dict of findings.


    For now, returns empty results.
    """
    deps = identify_repo_dependencies(repo_path)
    findings = run_repo_vulnerability_checks(deps)
    manifest = []
    return findings, manifest

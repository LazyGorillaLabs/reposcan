import os
import json
import tomli
from src.utils.logger import logger
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Any
from src.plugins.base_plugin import BasePlugin


class DependencyPlugin (BasePlugin):
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

    3. Don't trust the devs (especially ourselves):
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

    def scan(self, target_path: str) -> Dict[str, Any]:
        """
        1. Identify dependencies in repo
        2. Run vulnerability checks
        3. Return a dictionary of findings
        """
        deps = self.identify_repo_dependencies(target_path)
        
        total_deps = sum(len(dep_list) for lang_deps in deps.values() 
                        for dep_list in lang_deps.values())
        logger.info(f"Found {total_deps} total dependencies to check")
        
        findings = self.run_repo_vulnerability_checks(deps)

        # Build manifest of all package names
        manifest = []
        for lang_deps in deps.values():
            for file_deps in lang_deps.values():
                manifest.extend(pkg_name for pkg_name, _ in file_deps)
        manifest = list(dict.fromkeys(manifest))  # remove duplicates

        logger.info(f"Built manifest with {len(manifest)} unique package names")

        return {
            "dependency_findings": findings,  # The audit results
            "dependency_manifest": manifest   # The list of unique packages
        }

    def identify_file_dependencies(self, file_path: str) -> dict:
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


    def scan_file_dependencies(self, file_path: str, import_manifest: [str]) -> dict:
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

    def parse_requirements_txt(self, file_path: str) -> list:
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

    def parse_pyproject_toml(self, file_path: str) -> list:
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

    def parse_package_json(self, file_path: str) -> list:
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

    def identify_repo_dependencies(self, repo_path: str) -> dict:
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
        
        total_deps = 0
        
        repo_path = Path(repo_path)
        
        # Look for Python dependency files
        for req_file in repo_path.rglob('requirements.txt'):
            try:
                deps = self.parse_requirements_txt(str(req_file))
                if deps:
                    rel_path = str(req_file.relative_to(repo_path))
                    result["python"][rel_path] = deps
                    logger.info(f"Found requirements.txt at {rel_path} with {len(deps)} dependencies")
                    total_deps += len(deps)
            except Exception as e:
                print(f"Error processing {req_file}: {e}")
        
        for pyproject in repo_path.rglob('pyproject.toml'):
            try:
                deps = parse_pyproject_toml(str(pyproject))
                if deps:
                    rel_path = str(pyproject.relative_to(repo_path))
                    result["python"][rel_path] = deps
                    logger.info(f"Found pyproject.toml at {rel_path} with {len(deps)} dependencies")
                    total_deps += len(deps)
            except Exception as e:
                print(f"Error processing {pyproject}: {e}")
        
        # Look for Node.js dependency files
        for pkg_json in repo_path.rglob('package.json'):
            try:
                deps = self.parse_package_json(str(pkg_json))
                if deps:
                    rel_path = str(pkg_json.relative_to(repo_path))
                    result["node"][rel_path] = deps
                    logger.info(f"Found package.json at {rel_path} with {len(deps)} dependencies")
                    total_deps += len(deps)
            except Exception as e:
                print(f"Error processing {pkg_json}: {e}")
        
        return result


    def _run_pip_audit(self, deps: List[Tuple[str, str]]) -> List[dict]:
        """Run pip-audit on the given dependencies and return findings"""
        if not deps:
            logger.info("pip-audit requested with no dependencies to check. skipping.")
            return []
        
        # Create a temporary requirements.txt
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
            for pkg, ver in deps:
                if ver:
                    tmp.write(f"{pkg}=={ver}\n")
                else:
                    tmp.write(f"{pkg}\n")
            tmp_path = tmp.name

        findings = []
        try:
            logger.info(f"Attempting pip-audit on {len(deps)} dependencies")
            cmd = ['pip-audit', '--requirement', tmp_path, '--format', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Parse JSON output regardless of return code
            try:
                audit_data = json.loads(result.stdout)
                for dep in audit_data.get('dependencies', []):
                    vulns = dep.get('vulns', [])
                    if vulns:
                        findings.append({
                            "package": dep.get('name'),
                            "version": dep.get('version'),
                            "vulnerabilities": [{
                                "id": v.get('id'),
                                "description": v.get('description'),
                                "severity": "high"  # pip-audit doesn't provide severity
                            } for v in vulns]
                        })
            except json.JSONDecodeError:
                if "ResolutionImpossible" in result.stderr:
                    logger.error("pip-audit failed due to dependency conflicts")
                    findings.append({
                        "package": "requirements",
                        "version": "N/A", 
                        "vulnerabilities": [{
                            "id": "DEPENDENCY_CONFLICT",
                            "description": "Conflicting dependencies detected. This could mask security issues.",
                            "severity": "medium"
                        }]
                    })
                else:
                    logger.error(f"pip-audit failed: {result.stderr}")
                        
            if findings:
                logger.info(f"Found {len(findings)} dependency issues")
            return findings
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running dependency check: {str(e)}")
            return findings
        finally:
            os.unlink(tmp_path)

    def _run_npm_audit(self, deps: List[Tuple[str, str]]) -> List[dict]:
        """Run npm audit on the given dependencies and return findings"""
        if not deps:
            return []
        
        # Create a temporary package.json
        package_json = {
            "name": "temp-audit-pkg",
            "version": "1.0.0",
            "dependencies": {
                pkg: ver if ver else "latest" for pkg, ver in deps
            }
        }
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            pkg_path = os.path.join(tmp_dir, 'package.json')
            with open(pkg_path, 'w') as f:
                json.dump(package_json, f)
            
            try:
                # Run npm install and npm audit
                subprocess.run(['npm', 'install', '--prefix', tmp_dir], 
                             capture_output=True, check=True)
                result = subprocess.run(['npm', 'audit', '--json', '--prefix', tmp_dir],
                                     capture_output=True, text=True)
                
                try:
                    audit_data = json.loads(result.stdout)
                    vulnerabilities = []
                    
                    for adv in audit_data.get('advisories', {}).values():
                        vulnerabilities.append({
                            "package": adv.get('module_name'),
                            "version": adv.get('findings', [{}])[0].get('version'),
                            "vulnerabilities": [{
                                "id": adv.get('github_advisory_id') or adv.get('cve'),
                                "description": adv.get('overview'),
                                "severity": adv.get('severity')
                            }]
                        })
                    if vulnerabilities:
                        logger.info(f"npm audit found {len(vulnerabilities)} vulnerable packages")
                    return vulnerabilities
                except json.JSONDecodeError:
                    return []
                    
            except subprocess.CalledProcessError:
                return []

    def run_repo_vulnerability_checks(self, dependencies: dict) -> dict:
        """
        Given a dict of dependencies, run external tools or query APIs to find known vulnerabilities.
        """
        findings = {
            "dependency_issues": [],
            "total_vulnerabilities": 0,
            "vulnerable_packages": set()
        }
        
        # Check Python dependencies
        for file_deps in dependencies.get("python", {}).values():
            python_vulns = self._run_pip_audit(file_deps)
            findings["dependency_issues"].extend(python_vulns)
            findings["total_vulnerabilities"] += sum(len(v.get("vulnerabilities", [])) for v in python_vulns)
            findings["vulnerable_packages"].update(v.get("package") for v in python_vulns)
        
        # Check Node.js dependencies
        for file_deps in dependencies.get("node", {}).values():
            node_vulns = self._run_npm_audit(file_deps)
            findings["dependency_issues"].extend(node_vulns)
            findings["total_vulnerabilities"] += sum(len(v.get("vulnerabilities", [])) for v in node_vulns)
            findings["vulnerable_packages"].update(v.get("package") for v in node_vulns)
        
        # Convert set to list for JSON serialization
        findings["vulnerable_packages"] = list(findings["vulnerable_packages"])
        
        return findings

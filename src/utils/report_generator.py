# src/utils/report_generator.py
import os
from datetime import datetime
from typing import Dict, Any
from src.utils.logger import logger
from urllib.parse import urlparse

def get_report_filename(repo_input: str) -> str:
    """Generate a filename for the report based on repo name and date"""
    # Extract repo name from various input types
    if repo_input.startswith(('http://', 'https://')):
        parsed = urlparse(repo_input)
        path_parts = parsed.path.strip('/').split('/')
        repo_name = path_parts[-1] if path_parts else 'unknown'
    elif ':' in repo_input:
        # Handle pypi:package or github:user/repo format
        repo_name = repo_input.split(':')[1].split('/')[-1]
    else:
        # Local path - use directory/file name
        repo_name = os.path.basename(repo_input.rstrip('/'))

    # Clean up repo name and add timestamp
    repo_name = repo_name.replace('.git', '')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    return f"{repo_name}_scan_{timestamp}.md"

def generate_report(all_scan_results: Dict[str, Dict[str, Any]], output_dir: str = "reports") -> str:
    """
    Generate a human-readable Markdown report from the plugin-based results.
    all_scan_results structure:
    {
      "RegexPlugin": { ... },
      "BanditPlugin": { ... },
      "DependencyPlugin": { ... },
      ...
    }
    """
    logger.debug("Generating plugin-based report.")

    report_lines = []
    report_lines.append("# RepoScan Report\n")

    # We'll track some basic summary data
    plugin_issue_counts = {}
    
    # 1. QUICK PASS: Count "issues" to build a summary
    for plugin_name, plugin_data in all_scan_results.items():
        # We'll attempt a rough count of "issues" for summary
        issue_count = 0
        
        if plugin_name == "RegexPlugin":
            # plugin_data is dict: {file_path: {pattern_name: [matches...]}}
            # Let’s just count how many files had suspicious patterns
            issue_count = len(plugin_data)  # number of files with hits

        elif plugin_name == "BanditPlugin":
            # plugin_data is dict: {"bandit_issues": [list_of_issues]}
            bandit_issues = plugin_data.get("bandit_issues", [])
            issue_count = len(bandit_issues)

        elif plugin_name == "ESLintPlugin":
            # plugin_data might be something like {"eslint_issues": [issues]}
            eslint_issues = plugin_data.get("eslint_issues", [])
            issue_count = len(eslint_issues)

        elif plugin_name == "DependencyPlugin":
            # plugin_data is dict: {
            #   "dependency_findings": {"dependency_issues": [...], ...},
            #   "dependency_manifest": [...]
            # }
            dep_findings = plugin_data.get("dependency_findings", {})
            dep_issues = dep_findings.get("dependency_issues", [])
            issue_count = len(dep_issues)

        else:
            # Fallback attempt: 
            # if plugin_data is a dict, let's do something naive.
            # You can customize as needed.
            if isinstance(plugin_data, dict):
                issue_count = len(plugin_data)
        
        plugin_issue_counts[plugin_name] = issue_count

    # 2. Summary section
    total_plugins = len(all_scan_results)
    total_issues = sum(plugin_issue_counts.values())

    report_lines.append(f"**Summary:** {total_plugins} plugins ran. Detected potential issues in {total_issues} categories/files.\n")
    
    # 3. Detailed results, plugin-by-plugin
    for plugin_name, plugin_data in all_scan_results.items():
        report_lines.append(f"\n## Plugin: {plugin_name}\n")
        # If plugin_data is empty, we can say “No issues found”
        if not plugin_data:
            report_lines.append("No issues found by this plugin.\n")
            continue

        # Now handle each plugin type in a specialized way
        if plugin_name == "RegexPlugin":
            # plugin_data is structured like:
            # {
            #    "/path/to/file": { "exec_call": [...], "http_url": [...], ... },
            #    ...
            # }
            for file_path, pattern_dict in plugin_data.items():
                report_lines.append(f"### File: `{file_path}`\n")
                for pattern_name, match_list in pattern_dict.items():
                    # match_list is an array of matched strings
                    report_lines.append(f"- **{pattern_name}**: {len(match_list)} match(es).")
                    # If you want to show them, we can do something like:
                    # for match in match_list:
                    #     report_lines.append(f"  - `{match}`")
                report_lines.append("")  # blank line

        elif plugin_name == "BanditPlugin":
            # plugin_data might be: {"bandit_issues": [ {issue_key: val, ...}, ... ]}
            issues = plugin_data.get("bandit_issues", [])
            if not issues:
                report_lines.append("No Bandit issues found.\n")
            else:
                report_lines.append(f"Found {len(issues)} Bandit issue(s):\n")
                for issue in issues:
                    filename = issue.get("filename")
                    line_num = issue.get("line_number")
                    severity = issue.get("issue_severity")
                    issue_text = issue.get("issue_text", "")
                    test_name = issue.get("test_name", "")
                    report_lines.append(f"- **File**: `{filename}` (line {line_num}) | **{severity}**: {issue_text} (rule: {test_name})")

        elif plugin_name == "ESLintPlugin":
            # Suppose it's { "eslint_issues": [ {...}, ... ] }
            eslint_issues = plugin_data.get("eslint_issues", [])
            if not eslint_issues:
                report_lines.append("No ESLint issues found.\n")
            else:
                report_lines.append(f"Found {len(eslint_issues)} ESLint issue(s):\n")
                for issue in eslint_issues:
                    line = issue.get("line")
                    rule = issue.get("rule")
                    message = issue.get("message")
                    severity = issue.get("severity")
                    report_lines.append(f"- **Line {line}, {severity}**: {message} (rule: {rule})")
        
        elif plugin_name == "DependencyPlugin":
            # plugin_data: 
            # {
            #   "dependency_findings": {
            #       "dependency_issues": [...],
            #       "total_vulnerabilities": X,
            #       "vulnerable_packages": [...]
            #   },
            #   "dependency_manifest": [...]
            # }
            dep_findings = plugin_data.get("dependency_findings", {})
            dep_manifest = plugin_data.get("dependency_manifest", [])

            total_vulns = dep_findings.get("total_vulnerabilities", 0)
            dep_issues = dep_findings.get("dependency_issues", [])
            vulnerable_pkgs = dep_findings.get("vulnerable_packages", [])

            report_lines.append(f"**Dependency Manifest** ({len(dep_manifest)} total):\n")
            if dep_manifest:
                # list them
                for pkg in dep_manifest:
                    report_lines.append(f"- {pkg}")
            else:
                report_lines.append("No dependencies found.\n")

            report_lines.append(f"\n**Vulnerability Check**\n")
            report_lines.append(f"- Total Known Vulnerabilities: {total_vulns}")
            if dep_issues:
                report_lines.append(f"- Detailed issues ({len(dep_issues)}):")
                for issue in dep_issues:
                    pkg = issue.get("package")
                    version = issue.get("version")
                    vulns_list = issue.get("vulnerabilities", [])
                    report_lines.append(f"  - **{pkg}@{version}** has {len(vulns_list)} vulnerability(ies)")
                    for v in vulns_list:
                        vid = v.get("id", "N/A")
                        desc = v.get("description", "")
                        severity = v.get("severity", "unknown")
                        report_lines.append(f"    - {vid} ({severity}): {desc}")
            else:
                report_lines.append("No dependency-related issues found.")

        else:
            # Fallback for unknown plugin: just dump plugin_data
            report_lines.append("**Raw Plugin Data**:\n")
            report_lines.append(f"```\n{plugin_data}\n```")

    report_lines.append("\n---\n*End of Report*\n")
    report_content = "\n".join(report_lines)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    return report_content

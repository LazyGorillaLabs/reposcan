# project_root/src/utils/report_generator.py
from src.utils.logger import logger

def generate_report(scan_results: dict) -> str:
    logger.debug("Generating report from scan results.")
    report_lines = []
    report_lines.append("# Scan Report\n")
    
    # Handle dependency issues first if present
    if "Dependencies" in scan_results:
        report_lines.append("## Dependency Analysis\n")
        dep_issues = scan_results["Dependencies"].get("dependency_issues", [])
        if dep_issues:
            report_lines.append("### Known Vulnerabilities Found:\n")
            for issue in dep_issues:
                pkg = issue.get("package", "Unknown")
                version = issue.get("version", "Unknown")
                report_lines.append(f"- Package: **{pkg}** (version: {version})")
                for vuln in issue.get("vulnerabilities", []):
                    vuln_id = vuln.get("id", "No ID")
                    severity = vuln.get("severity", "unknown")
                    desc = vuln.get("description", "No description available")
                    report_lines.append(f"  - **{vuln_id}** ({severity}): {desc}")
                report_lines.append("")
            report_lines.append("")
        else:
            report_lines.append("No dependency vulnerabilities found.\n")
    
    # Handle file-specific findings
    suspicious_count = 0
    report_lines.append("Static Code Analysis\n")
    for file_path, patterns_found in scan_results.items():
        if file_path != "Dependencies" and patterns_found:
            suspicious_count += 1
            report_lines.append(f"## {file_path}")
            for pattern_name, matches in patterns_found.items():
                report_lines.append(f"- **{pattern_name}**: Found {len(matches)} occurrences.")
            report_lines.append("")

    # Add summary
    if suspicious_count == 0:
        report_lines.insert(1, "No suspicious patterns found in files.\n")
        logger.info("No suspicious patterns detected in files.")
    else:
        summary = f"**Summary:** {suspicious_count} files with flagged patterns.\n"
        report_lines.insert(1, summary)
        logger.info(f"Flagged patterns found in {suspicious_count} files.")

    return "\n".join(report_lines)

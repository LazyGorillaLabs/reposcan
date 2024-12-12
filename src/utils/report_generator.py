# project_root/src/utils/report_generator.py
"""
Generates a simple report from the scan results.
"""

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
            report_lines.append("")  # blank line

    if suspicious_count == 0:
        report_lines.insert(1, "No suspicious patterns found.\n")
    else:
        report_lines.insert(1, f"**Summary:** {suspicious_count} files with suspicious patterns.\n")

    return "\n".join(report_lines)


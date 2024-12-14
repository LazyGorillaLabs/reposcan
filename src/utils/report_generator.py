# project_root/src/utils/report_generator.py
from src.utils.logger import logger

def generate_report(scan_results: dict) -> str:
    logger.debug("Generating report from scan results.")
    report_lines = []
    report_lines.append("# Scan Report\n")
    suspicious_count = 0
    for file_path, patterns_found in scan_results.items():
        if patterns_found:
            suspicious_count += 1
            report_lines.append(f"## {file_path}")
            for pattern_name, matches in patterns_found.items():
                report_lines.append(f"- **{pattern_name}**: Found {len(matches)} occurrences.")
            report_lines.append("")

    if suspicious_count == 0:
        report_lines.insert(1, "No suspicious patterns found.\n")
        logger.info("No suspicious patterns detected.")
    else:
        summary = f"**Summary:** {suspicious_count} files with flagged patterns.\n"
        report_lines.insert(1, summary)
        logger.info(f"Flagged patterns found in {suspicious_count} files.")

    return "\n".join(report_lines)

# project_root/src/patterns/javascript_patterns.py
"""
JavaScript/Node.js-specific suspicious patterns.

Focus on requires that enable networking or child processes:
- net for low-level networking
- child_process for spawning external processes
- nodemailer for email sending
- new Function() for dynamic code execution
"""

import re

JAVASCRIPT_SUSPICIOUS_PATTERNS = {
    "js_require_net": re.compile(r"require\(['\"]net['\"]\)"),
    "js_require_child_process": re.compile(r"require\(['\"]child_process['\"]\)"),
    "js_require_nodemailer": re.compile(r"require\(['\"]nodemailer['\"]\)"),
    "js_new_function_call": re.compile(r"new\s+Function\s*\("),
}


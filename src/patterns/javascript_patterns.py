# project_root/src/patterns/javascript_patterns.py
"""
JavaScript/Node.js/WScript-specific suspicious patterns.

Previously we focused on Node.js constructs like:
- require('net')
- require('child_process')
- require('nodemailer')
- new Function()

Now we add patterns for Windows Script Host (WSH) and ActiveX usage, 
as we encountered malicious scripts that rely on WScript, ActiveXObject,
and the Scripting.FileSystemObject for malicious file manipulation.

These patterns are heuristic and will likely produce false positives in 
legitimate automation scripts. However, their presence in suspicious contexts 
is often a strong indicator.
"""

import re

JAVASCRIPT_SUSPICIOUS_PATTERNS = {
    # Existing JS patterns:
    "js_require_net": re.compile(r"require\(['\"]net['\"]\)"),
    "js_require_child_process": re.compile(r"require\(['\"]child_process['\"]\)"),
    "js_require_nodemailer": re.compile(r"require\(['\"]nodemailer['\"]\)"),
    "js_new_function_call": re.compile(r"new\s+Function\s*\("),

    # New WSH/ActiveX related patterns:
    # ActiveXObject often used in malicious WScript/JScript code
    "js_activexobject": re.compile(r"\bActiveXObject\s*\("),
    
    # Scripting.FileSystemObject is a WSH object often abused by malware
    "js_fso": re.compile(r"Scripting\.FileSystemObject"),
    
    # WScript usage (e.g., WScript.Sleep, WScript.ScriptFullName) can be suspicious 
    # in malicious scripts that aim to run outside browser context
    "js_wscript": re.compile(r"\bWScript\b"),
    
    # Shell.Application could indicate shell access & system manipulation
    "js_shell_application": re.compile(r"Shell\.Application"),
    
    # Document write in a WSH context might be suspicious (depends on environment)
    # We'll flag document.write as suspicious in a JS script outside a browser environment.
    # This is heuristic; it may be safe in actual browser code.
    "js_document_write": re.compile(r"\bdocument\.write\s*\("),
}

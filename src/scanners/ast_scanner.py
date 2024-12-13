# project_root/src/scanners/ast_scanner.py
"""
AST-based scanner for Python files.

This module parses Python source code into an AST and looks for suspicious constructs
that may not be easily identified with regex alone.

Initial Targets:
- Calls to eval, exec, __import__ with non-constant arguments.
- Dynamically constructed imports.

In the future, this can be expanded to detect more nuanced suspicious patterns.
"""

import ast
from src.utils.logger import logger

class PythonAstScanner(ast.NodeVisitor):
    """
    Visits Python AST nodes and flags suspicious patterns.

    Current Heuristics:
    - Eval/Exec/__import__ calls with non-literal arguments.
      For example: eval(something) where 'something' is not a string literal directly.
    - __import__ calls that construct the module name dynamically.
    """

    def __init__(self):
        self.findings = {}

    def add_finding(self, pattern_name, node_info):
        if pattern_name not in self.findings:
            self.findings[pattern_name] = []
        self.findings[pattern_name].append(node_info)

    def visit_Call(self, node):
        """
        Check function calls. We're interested in calls to:
        - eval
        - exec
        - __import__
        
        Specifically, we flag them if their arguments are not simple string constants.
        """
        func_name = self.get_func_name(node)
        if func_name in ("eval", "exec", "__import__"):
            # Check arguments
            if node.args:
                # If the first argument is not a string literal, consider it suspicious.
                # For __import__, we consider dynamic module names suspicious.
                first_arg = node.args[0]
                if not self.is_string_literal(first_arg):
                    self.add_finding("ast_dynamic_eval_exec_import", {
                        "line": node.lineno,
                        "col": node.col_offset,
                        "function": func_name,
                        "reason": "Non-literal argument to {}".format(func_name)
                    })
        # Continue visiting other nodes
        self.generic_visit(node)

    def get_func_name(self, node):
        """ Attempt to extract a function name from a Call node. """
        # func could be a Name, Attribute, etc.
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def is_string_literal(self, node):
        """
        Check if a node represents a simple string literal.
        For Python 3.8+, ast.Constant is used for literals. For older versions, Str nodes are used.
        We'll assume Python 3.8+ for simplicity.
        """
        if isinstance(node, ast.Constant):
            return isinstance(node.value, str)
        elif isinstance(node, ast.Str):  # For older Python versions
            return True
        return False

def scan_python_file_with_ast(file_path: str) -> dict:
    """
    Parse a Python file into an AST and use PythonAstScanner to find suspicious patterns.
    Returns a dictionary of findings similar to the pattern scanner.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path} for AST scan: {e}")
        return {"error_reading_ast": [str(e)]}

    try:
        tree = ast.parse(content, filename=file_path)
    except SyntaxError as se:
        # If the code doesn't parse, we just log and return empty.
        logger.warning(f"Syntax error parsing {file_path}: {se}")
        return {}

    scanner = PythonAstScanner()
    scanner.visit(tree)
    return scanner.findings


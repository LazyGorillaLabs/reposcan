"""
LLM-based code analysis plugin that uses language models to detect potential issues.
"""

import os
from typing import Dict, Any
from src.plugins.base_plugin import BasePlugin
from src.utils.logger import logger

class LLMPlugin(BasePlugin):
    """
    A scanner that uses LLM-based analysis to detect suspicious code patterns.
    
    This plugin:
    - Lazy loads the LiteLLM library
    - Processes files individually through LLM analysis
    - Aggregates findings into a standardized format
    """

    def __init__(self):
        self._llm = None  # Lazy load LiteLLM
        self._analyzer = None  # Will hold reference to LLM analyzer

    def _ensure_llm_loaded(self):
        """Lazy load LiteLLM and analyzer only when needed"""
        if self._llm is None:
            try:
                # Lazy import to avoid loading unless needed
                from src.llm.llm_analyzer import LLMAnalyzer
                self._analyzer = LLMAnalyzer()
            except ImportError as e:
                logger.error(f"Failed to import LLM dependencies: {e}")
                raise

    def scan(self, target_path: str) -> Dict[str, Any]:
        """
        Perform LLM-based scanning on `target_path`.
        Returns a dictionary of findings.
        """
        findings = {}
        
        # 1. If target_path is a directory, gather all the relevant files
        file_list = []
        if os.path.isdir(target_path):
            for root, dirs, files in os.walk(target_path):
                for f in files:
                    # TODO: Add file extension filtering if needed
                    file_list.append(os.path.join(root, f))
        elif os.path.isfile(target_path):
            file_list = [target_path]
        else:
            logger.error(f"LLMPlugin: '{target_path}' is neither file nor directory")
            return findings

        # 2. Ensure LLM is loaded before processing
        try:
            self._ensure_llm_loaded()
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            return findings

        # 3. Have LLM module estimate cost based on model and total embeddings for the filtered project files
        #    Give user option to proceed or skip the plugin before proceeding. 
        #    Maybe one day options to change model or abort full run, but save for future dev

        # 4. Process each file individually
        for file_path in file_list:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                    # Process through LLM analyzer
                    file_findings = self._analyzer.analyze_code(content)
                    
                    if file_findings:
                        findings[file_path] = file_findings
                        
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                findings.setdefault(file_path, {})["error_processing"] = str(e)

        return findings

from abc import ABC, abstractmethod
from typing import Dict, Any

class BasePlugin(ABC):
    """
    Abstract base class defining the contract for all scanning plugins.
    """

    @abstractmethod
    def scan(self, target_path: str) -> Dict[str, Any]:
        """
        Perform the plugin's scanning on `target_path`.
        Returns a dictionary of findings.
        """
        pass

    @property
    def name(self) -> str:
        """
        Optional: Return the name of this plugin for logging/reporting.
        """
        return self.__class__.__name__


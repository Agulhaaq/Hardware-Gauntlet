"""Base scanner interface for Hardware Gauntlet."""

from abc import ABC, abstractmethod
from typing import Any


class BaseScanner(ABC):
    """Abstract base class that all hardware scanners implement."""

    @abstractmethod
    def scan(self) -> Any:
        """Execute hardware scanning and return structured model."""
        pass

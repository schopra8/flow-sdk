from abc import ABC, abstractmethod
from typing import Any, Dict, List
from rich.console import Console


class Formatter(ABC):
    """Abstract base class for formatters.

    Provides a console for generating rich text output and defines an
    abstract method for formatting the status of bids and instances.
    """

    def __init__(self) -> None:
        """Initializes Formatter with a console for output."""
        self.console = Console()

    @abstractmethod
    def format_status(
        self, bids: List[Dict[str, Any]], instances: List[Dict[str, Any]]
    ) -> None:
        """Formats and displays the status of bids and instances.

        Args:
            bids: A list of dictionaries containing bid information.
            instances: A list of dictionaries containing instance information.
        """
        pass

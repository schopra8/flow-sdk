from typing import List, Optional


class ConfigParserError(Exception):
    """Custom exception class for ConfigParser errors.

    Attributes:
        message: The error message.
        errors: A list of specific error messages.
    """

    def __init__(self, message: str, errors: Optional[List[str]] = None) -> None:
        """Initializes ConfigParserError with a message and optional errors.

        Args:
            message: The error message.
            errors: A list of specific error messages.
        """
        super().__init__(message)
        self.errors = errors or []

    def __str__(self) -> str:
        """Return the string representation of the error.

        Returns:
            The error message with any additional errors.
        """
        error_messages = "; ".join(self.errors)
        return (
            f"{super().__str__()} Errors: {error_messages}"
            if self.errors
            else super().__str__()
        )

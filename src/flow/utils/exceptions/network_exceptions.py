class NetworkError(Exception):
    """Exception raised for network-related errors."""


class TimeoutError(NetworkError):
    """Exception raised when a network operation times out."""

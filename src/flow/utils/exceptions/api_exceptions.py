class APIError(Exception):
    """Exception raised for API request failures."""


class InvalidResponseError(APIError):
    """Exception raised when an API response cannot be decoded as JSON."""


class NoMatchingAuctionsError(APIError):
    """Exception raised when no matching auctions are found."""


class BidSubmissionError(APIError):
    """Exception raised when bid submission fails."""

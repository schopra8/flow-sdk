class AuthenticationError(Exception):
    """Exception raised for authentication failures."""


class InvalidCredentialsError(AuthenticationError):
    """Exception raised when invalid credentials are provided."""

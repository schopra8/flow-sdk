# TODO(jaredquincy): Need to significantly expand the exception handling used.
# Defining custom exceptions used in the tests and throughout.


class APIError(Exception):
    """Raised for API request failures."""


class AuthenticationError(Exception):
    """Raised for authentication failures."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when invalid credentials are provided."""


class NetworkError(AuthenticationError):
    """Raised when a network error occurs during authentication."""


class TimeoutError(AuthenticationError):
    """Raised when the authentication request times out."""


class NoMatchingAuctionsError(Exception):
    """Raised when no matching auctions are found."""


class BidSubmissionError(Exception):
    """Raised when bid submission fails."""


class StorageError(Exception):
    """Base exception for storage-related errors."""


class DiskNotFoundError(StorageError):
    """Raised when a specified disk is not found."""

    def __init__(self, disk_name: str):
        """Initializes a DiskNotFoundError with the specified disk name.

        Args:
            disk_name: The name of the disk that was not found.
        """
        super().__init__(f"Persistent disk '{disk_name}' not found.")


class DiskCreationError(StorageError):
    """Raised when disk creation fails."""

    def __init__(self, reason: str):
        """Initializes a DiskCreationError with the specified reason.

        Args:
            reason: The reason disk creation failed.
        """
        super().__init__(f"Failed to create persistent disk: {reason}")


class DiskMountError(StorageError):
    """Raised when mounting a disk fails."""

    def __init__(self, disk_name: str, mount_point: str, reason: str):
        """Initializes a DiskMountError with disk name, mount point, and reason.

        Args:
            disk_name: The name of the disk that failed to mount.
            mount_point: The target directory or location for mounting the disk.
            reason: The reason the disk mounting failed.
        """
        message = f"Failed to mount disk '{disk_name}' at '{mount_point}': {reason}"
        super().__init__(message)


class DiskFormattingError(StorageError):
    """Raised when formatting a disk fails."""

    def __init__(self, device_name: str, reason: str):
        """Initializes a DiskFormattingError with device name and reason.

        Args:
            device_name: The name of the device that failed to format.
            reason: The reason the disk formatting failed.
        """
        message = f"Failed to format device '{device_name}': {reason}"
        super().__init__(message)


class QuotaExceededError(StorageError):
    """Raised when storage quota is exceeded."""

    def __init__(self, quota_limit: int):
        """Initializes a QuotaExceededError with the quota limit.

        Args:
            quota_limit: The maximum storage quota in gigabytes.
        """
        super().__init__(f"Storage quota of {quota_limit} GB exceeded.")


class RegionNotFoundError(StorageError):
    """Raised when the specified region is not found."""

    def __init__(self, region_id: str):
        """Initializes a RegionNotFoundError with the region identifier.

        Args:
            region_id: The identifier of the region that was not found.
        """
        super().__init__(f"Region '{region_id}' not found.")


class ProjectNotFoundError(StorageError):
    """Raised when the specified project is not found."""

    def __init__(self, project_id: str):
        """Initializes a ProjectNotFoundError with the project identifier.

        Args:
            project_id: The identifier of the project that was not found.
        """
        super().__init__(f"Project '{project_id}' not found.")


class UnsupportedDiskInterfaceError(StorageError):
    """Raised when an unsupported disk interface is specified."""

    def __init__(self, disk_interface: str):
        """Initializes an UnsupportedDiskInterfaceError with the disk interface.

        Args:
            disk_interface: The disk interface that is unsupported.
        """
        super().__init__(f"Unsupported disk interface '{disk_interface}'.")


class InvalidStorageConfigurationError(StorageError):
    """Raised when the storage configuration is invalid."""

    def __init__(self, message: str):
        """Initializes an InvalidStorageConfigurationError with the given message.

        Args:
            message: Additional information about the invalid configuration.
        """
        super().__init__(f"Invalid storage configuration: {message}")


class AsyncOperationError(StorageError):
    """Raised when an asynchronous operation fails."""

    def __init__(self, operation: str, reason: str):
        """Initializes an AsyncOperationError with operation name and reason.

        Args:
            operation: The name or ID of the asynchronous operation.
            reason: The reason the async operation failed.
        """
        super().__init__(f"Async operation '{operation}' failed: {reason}")


class InvalidResponseError(Exception):
    """Raised when an API response cannot be decoded as JSON."""

    def __init__(self, message: str = "Invalid JSON response."):
        """Initializes an InvalidResponseError with a specific message.

        Args:
            message: A custom message describing the invalid response error.
        """
        super().__init__(message)

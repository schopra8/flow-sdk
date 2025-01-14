class StorageError(Exception):
    """Base exception for storage-related errors."""


class DiskNotFoundError(StorageError):
    """Exception raised when a specified disk is not found."""


class DiskCreationError(StorageError):
    """Exception raised when disk creation fails."""


class DiskMountError(StorageError):
    """Exception raised when mounting a disk fails."""


class DiskFormattingError(StorageError):
    """Exception raised when formatting a disk fails."""


class QuotaExceededError(StorageError):
    """Exception raised when storage quota is exceeded."""


class RegionNotFoundError(StorageError):
    """Exception raised when the specified region is not found."""


class ProjectNotFoundError(StorageError):
    """Exception raised when the specified project is not found."""


class UnsupportedDiskInterfaceError(StorageError):
    """Exception raised when an unsupported disk interface is specified."""


class InvalidStorageConfigurationError(StorageError):
    """Exception raised when the storage configuration is invalid."""


class AsyncOperationError(StorageError):
    """Exception raised when an asynchronous operation fails."""

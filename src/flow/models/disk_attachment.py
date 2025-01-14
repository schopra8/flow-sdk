from typing import Optional
from pydantic import BaseModel, field_validator, ConfigDict


class DiskAttachment(BaseModel):
    """Represents a disk attachment in a bid.

    Attributes:
        disk_id: The unique identifier for the disk.
        name: The name of the disk (as required by the API).
        volume_name: The display name of the disk, or None if no display name is
            provided.
        disk_interface: The type of disk interface, which can be 'Block' or 'File'.
        region_id: The region ID where the disk is located, or None if not specified.
        size: The size of the disk in gigabytes or terabytes.
        size_unit: The unit of measurement for the disk size ('gb' or 'tb'). Defaults
            to 'gb'.
    """

    model_config = ConfigDict(populate_by_name=True)

    disk_id: str
    name: str
    volume_name: Optional[str] = None
    disk_interface: str
    region_id: Optional[str] = None
    size: int
    size_unit: Optional[str] = "gb"

    @field_validator("disk_id", "name")
    def validate_non_empty_fields(cls, value: str) -> str:
        """Validates that the provided field is not empty or whitespace.

        Args:
            value: The field value to validate.

        Returns:
            The validated value.

        Raises:
            ValueError: If the field value is empty or whitespace.
        """
        if not value.strip():
            raise ValueError("Field cannot be empty or whitespace.")
        return value

    @field_validator("disk_interface")
    def validate_disk_interface(cls, value: str) -> str:
        """Validates that the disk interface is either 'Block' or 'File'.

        Args:
            value: The disk interface to validate.

        Returns:
            The capitalized disk interface.

        Raises:
            ValueError: If the disk interface is not 'Block' or 'File'.
        """
        allowed_interfaces = {"Block", "File"}
        normalized = value.capitalize()
        if normalized not in allowed_interfaces:
            raise ValueError(f"disk_interface must be one of {allowed_interfaces}.")
        return normalized

    @field_validator("size")
    def validate_size(cls, value: int) -> int:
        """Validates that the size is greater than 0.

        Args:
            value: The size value to validate.

        Returns:
            The validated size value.

        Raises:
            ValueError: If the size is less than or equal to 0.
        """
        if value <= 0:
            raise ValueError("size must be greater than 0.")
        return value

    @field_validator("size_unit", mode="before")
    def validate_size_unit(cls, value: Optional[str]) -> str:
        """Validates the size unit, defaulting to 'gb' if None.

        Args:
            value: The size unit to validate, which may be None.

        Returns:
            The validated size unit value.

        Raises:
            ValueError: If the size unit is not 'gb' or 'tb'.
        """
        allowed_units = {"gb", "tb"}
        if value is None:
            return "gb"
        value_lower = value.lower()
        if value_lower not in allowed_units:
            raise ValueError(f"size_unit must be one of {allowed_units}.")
        return value_lower

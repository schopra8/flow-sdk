from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DiskResponse(BaseModel):
    """Represents a disk resource retrieved or created via the Storage API.

    Attributes:
        disk_id: The unique identifier for the disk.
        name: The name of the disk.
        volume_name: The volume name, or None if not provided.
        disk_interface: The interface used by the disk.
        region_id: The region where the disk is located.
        size: The size of the disk in gigabytes or terabytes, or None if not specified.
        size_unit: The unit of measurement for the size field, e.g., 'gb' or 'tb'.
    """

    model_config = ConfigDict(populate_by_name=True)

    disk_id: str = Field(..., alias="id")
    name: str
    volume_name: Optional[str] = None
    disk_interface: str = Field(..., alias="interface")
    region_id: str
    size: Optional[int] = Field(None, alias="size")
    size_unit: Optional[str] = Field(None, alias="unit")


class StorageQuotaResponse(BaseModel):
    """Represents storage quota information returned by the API.

    Attributes:
        total_storage: The total storage quota allocated.
        used_storage: The amount of storage consumed.
        unit: The measurement unit for the quota values.
    """

    # TODO: integrate with the new storage client and exception handling

    model_config = ConfigDict(populate_by_name=True)

    total_storage: int = Field(..., alias="total_quota")
    used_storage: int = Field(..., alias="quota_used")
    unit: str = Field(..., alias="units")


class RegionResponse(BaseModel):
    """Represents a region within the Storage API's ecosystem.

    Attributes:
        region_id: The unique identifier for the region.
        name: The name of the region.
    """

    model_config = ConfigDict(populate_by_name=True)

    region_id: str = Field(
        ..., alias="id", description="Unique identifier for the region"
    )
    name: str = Field(..., alias="name")

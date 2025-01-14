from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class BaseInstanceResponseModel(BaseModel):
    """Base model representing the raw instance response.

    Attributes:
      cluster_id: The cluster ID associated with the instance.
      connection_info: Connection-related information.
      control_plane_instance: Flag indicating if it's a control plane instance.
      created_ts: Timestamp when the instance was created.
      disks: List of disks attached to the instance.
      end_date: The end date of the instance lifecycle.
      instance_id: The unique identifier of the instance.
      instance_status: The status of the instance.
      instance_type_id: The type identifier of the instance.
      managed_customer_cluster_id: The managed customer cluster ID.
      metadata: Additional metadata for the instance.
      name: The name of the instance.
      order_id: The order identifier associated with the instance.
      order_type: The type of the order.
      public_keys: List of public keys.
      ssh_destination: SSH destination string.
      start_date: The start date of the instance lifecycle.
    """

    cluster_id: Optional[str] = None
    connection_info: Optional[Any] = None
    control_plane_instance: Optional[bool] = None
    created_ts: Optional[datetime] = Field(default=None, alias="created_ts")
    disks: Optional[List[str]] = None
    end_date: Optional[datetime] = None
    instance_id: Optional[str] = None
    instance_status: Optional[str] = None
    instance_type_id: Optional[str] = None
    managed_customer_cluster_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    name: Optional[str] = None
    order_id: Optional[str] = None
    order_type: Optional[str] = None
    public_keys: Optional[List[str]] = None
    ssh_destination: Optional[str] = None
    start_date: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True, arbitrary_types_allowed=True, frozen=True
    )

    @field_serializer("created_ts", "end_date", "start_date")
    def _serialize_datetime_fields(self, dt: Optional[datetime]) -> Optional[str]:
        return dt.isoformat() if dt else None


class Instance(BaseInstanceResponseModel):
    """Model representing an instance with additional properties.

    Attributes:
      instance_type: The type of the instance, derived from instance_type_id.
      region: The region where the instance is located.
      ip_address: The IP address of the instance.
      category: The category of the instance.
    """

    instance_type: Optional[str] = None
    region: Optional[str] = None
    ip_address: Optional[str] = None
    category: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True, arbitrary_types_allowed=True, frozen=False
    )

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization method to set additional attributes."""
        if self.instance_type is None:
            self.instance_type = "---"
        if self.ip_address is None:
            self.ip_address = self.ssh_destination or "---"
        if self.category is None:
            self.category = (self.order_type or "N/A").lower()
        if self.region is None:
            if self.metadata and "region" in self.metadata:
                self.region = self.metadata["region"]
            else:
                self.region = "---"

        if (
            not self.ip_address or self.ip_address.strip() == "---"
        ) and self.connection_info:
            if (
                isinstance(self.connection_info, dict)
                and "ip_address" in self.connection_info
            ):
                self.ip_address = self.connection_info["ip_address"]


class SpotInstance(Instance):
    """Represents a spot instance in the system.

    Attributes:
      spot_bid_id: The bid identifier associated with the spot instance.
    """

    spot_bid_id: Optional[str] = None


class ReservedInstance(Instance):
    """Represents a reserved instance in the system.

    Attributes:
      reservation_id: The reservation identifier associated with the reserved
        instance.
    """

    reservation_id: Optional[str] = None


class LegacyInstance(Instance):
    """Represents a legacy instance in the system.

    Additional legacy-specific fields can be added here.
    """

    pass


class BlockInstance(Instance):
    """Represents a block instance in the system.

    Additional block-specific fields can be added here.
    """

    pass


class ControlInstance(Instance):
    """Represents a control instance in the system.

    Additional control-specific fields can be added here.
    """

    pass

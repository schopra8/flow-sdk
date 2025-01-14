from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
from flow.models.bid_disk_attachment import BidDiskAttachment


class BidPayload(BaseModel):
    """Represents the payload for submitting a bid.

    Attributes:
        cluster_id: The identifier of the cluster.
        instance_quantity: The number of instances to request. Must be greater than 0.
        instance_type_id: The type identifier of the instance.
        limit_price_cents: The maximum price (in cents) the user is willing to pay. Must be greater than 0.
        order_name: The name of the bid order.
        project_id: The identifier of the project.
        ssh_key_ids: A list of SSH key identifiers associated with the bid. Must not be empty.
        startup_script: The startup script to execute on instance startup, if any.
        user_id: The identifier of the user submitting the bid.
        disk_attachments: An optional list of disk attachments associated with the bid.
    """

    cluster_id: str
    instance_quantity: int = Field(gt=0)
    instance_type_id: str
    limit_price_cents: int = Field(gt=0)
    order_name: str
    project_id: str
    ssh_key_ids: List[str] = Field(min_length=1)
    startup_script: Optional[str] = None
    user_id: str
    disk_attachments: Optional[List[BidDiskAttachment]] = []

    @field_validator(
        "cluster_id", "instance_type_id", "order_name", "project_id", "user_id"
    )
    def validate_not_empty(cls, value: str) -> str:
        """Validates that the given string field is not empty or whitespace.

        Args:
            value: The string value to validate.

        Returns:
            The validated string if it is not empty or whitespace.

        Raises:
            ValueError: If the string is empty or contains only whitespace.
        """
        if not value.strip():
            raise ValueError("Field cannot be empty or whitespace.")
        return value

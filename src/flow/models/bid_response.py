from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator


class BidResponse(BaseModel):
    """Represents what the server sends back after a successful place_bid."""

    id: str
    name: Optional[str] = None
    cluster_id: str
    instance_quantity: int
    instance_type_id: str
    limit_price_cents: int
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    disk_ids: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None

    @field_validator("id", "cluster_id", "instance_type_id")
    def not_empty_fields(cls, value: str) -> str:
        """Raises ValueError if the field is empty or whitespace."""
        if not value.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return value

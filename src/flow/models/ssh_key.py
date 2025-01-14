from typing import Optional
from pydantic import BaseModel, field_validator


class SshKey(BaseModel):
    """Represents a single SSH key."""

    id: str
    name: Optional[str] = None
    fingerprint: Optional[str] = None
    public_key: Optional[str] = None
    private_key: Optional[str] = None
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    created_at: Optional[str] = None

    @field_validator("id")
    def not_empty_id(cls, value: str) -> str:
        """Raises ValueError if the SshKey 'id' is empty or whitespace."""
        if not value.strip():
            raise ValueError("SshKey 'id' cannot be empty")
        return value

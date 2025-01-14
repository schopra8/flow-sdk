from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, field_validator


class User(BaseModel):
    """Represents the currently authenticated user."""

    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    created_ts: Optional[str] = None
    fid: Optional[str] = None
    function: Optional[str] = None
    organization_id: Optional[str] = None
    organization_role: Optional[str] = None
    organizations: Optional[Any] = None
    title: Optional[str] = None
    user_name: Optional[str] = None

    model_config = ConfigDict(extra="allow")  # or "ignore"

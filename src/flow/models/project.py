from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Project(BaseModel):
    """Represents a project in the system.

    Attributes:
        id: The unique identifier for the project.
        name: The name of the project.
        created_at: When the project was created (if available).
    """

    id: str
    name: str
    created_at: Optional[datetime] = None

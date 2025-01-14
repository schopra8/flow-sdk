from typing import List, Optional

from pydantic import BaseModel


class Bid(BaseModel):
    """Represents a bid in the system.

    Attributes:
        id: The unique identifier for the bid.
        name: The name of the bid.
        status: The current status of the bid.
        created_at: The timestamp when the bid was created.
        deactivated_at: The timestamp when the bid was deactivated, if applicable.
        limit_price_cents: The limit price in cents for the bid.
        instance_quantity: The number of instances requested.
        instance_type_id: The identifier of the instance type.
        cluster_id: The identifier of the cluster.
        project_id: The identifier of the project.
        ssh_key_ids: A list of SSH key identifiers associated with the bid.
        startup_script: The startup script to run on instance startup.
        user_id: The identifier of the user who created the bid.
        disk_ids: A list of disk identifiers associated with the bid.
    """

    id: str
    name: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    deactivated_at: Optional[str] = None
    limit_price_cents: Optional[int] = None
    instance_quantity: Optional[int] = None
    instance_type_id: Optional[str] = None
    cluster_id: Optional[str] = None
    project_id: Optional[str] = None
    ssh_key_ids: Optional[List[str]] = None
    startup_script: Optional[str] = None
    user_id: Optional[str] = None
    disk_ids: Optional[List[str]] = None

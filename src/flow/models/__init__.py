# Domain-focused imports for aggregator.
from .auction import Auction
from .bid import Bid
from .bid_payload import BidPayload
from .bid_disk_attachment import BidDiskAttachment
from .disk_attachment import DiskAttachment

# Instance-related classes
from .instance import (
    Instance,
    SpotInstance,
    ReservedInstance,
    LegacyInstance,
    BlockInstance,
    ControlInstance,
)

from .instance_type import DetailedInstanceType
from .project import Project
from .storage_responses import (
    DiskResponse,
    RegionResponse,
    StorageQuotaResponse,
)

# Bringing in PersistentStorageCreate and PersistentStorage from config/models
from flow.task_config.models import PersistentStorageCreate, PersistentStorage

from .user import User
from .ssh_key import SshKey
from .bid_response import BidResponse

__all__ = [
    "Auction",
    "Bid",
    "BidPayload",
    "BidDiskAttachment",
    "DiskAttachment",
    "Instance",
    "SpotInstance",
    "ReservedInstance",
    "LegacyInstance",
    "BlockInstance",
    "ControlInstance",
    "DetailedInstanceType",
    "Project",
    "DiskResponse",
    "RegionResponse",
    "StorageQuotaResponse",
    "User",
    "SshKey",
    "BidResponse",
    "PersistentStorageCreate",
    "PersistentStorage",
]

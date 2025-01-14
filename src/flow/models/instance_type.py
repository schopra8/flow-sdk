from typing import Optional

from pydantic import BaseModel


class InstanceType(BaseModel):
    """Represents an instance type in the system.

    Attributes:
      id: The unique identifier for the instance type.
      name: The name of the instance type.
    """

    id: str
    name: str


class DetailedInstanceType(BaseModel):
    """Provides a thorough representation of an instance type.

    Describes vCPUs, GPUs, memory, specialized hardware, etc.

    Attributes:
      id: The unique identifier for the instance type.
      name: The name of the instance type.
      num_cpus: The number of CPUs. Defaults to None.
      num_gpus: The number of GPUs. Defaults to None.
      memory_gb: The amount of memory in gigabytes. Defaults to None.
      architecture: The CPU architecture. Defaults to None.
    """

    id: str
    name: str
    num_cpus: Optional[int] = None
    num_gpus: Optional[int] = None
    memory_gb: Optional[int] = None
    architecture: Optional[str] = None

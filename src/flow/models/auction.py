from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Auction(BaseModel):
    """Represents an auction for compute resources.

    Attributes:
        id: Unique identifier for the auction.
        gpu_type: Type of GPU being offered.
        inventory_quantity: Number of GPUs available.
        intranode_interconnect: Type of connection between GPUs within a node.
        internode_interconnect: Type of connection between nodes.
        instance_type_id: Instance type ID of the GPU.
        fcp_instance: Optional string describing the FCP instance.
        last_price: The last recorded price for the auction.
        region: The region name as returned by the server.
        region_id: The region identifier.
        resource_specification_id: The resource specification identifier.
    """

    id: str = Field(..., alias="cluster_id")
    gpu_type: Optional[str] = None
    inventory_quantity: Optional[int] = None
    num_gpus: Optional[int] = Field(None, alias="num_gpu")
    intranode_interconnect: Optional[str] = None
    internode_interconnect: Optional[str] = None
    fcp_instance: Optional[str] = None
    instance_type_id: Optional[str] = None
    last_price: Optional[float] = None
    region: Optional[str] = None
    region_id: Optional[str] = Field(None, alias="region_id")
    resource_specification_id: Optional[str] = None

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        alias_generator=None,
    )

    @property
    def cluster_id(self) -> str:
        """Alias for the id attribute to maintain compatibility.

        Returns:
            str: The cluster identifier.
        """
        return self.id

    @classmethod
    def from_api_response(cls, data: dict) -> "Auction":
        """Creates an Auction instance from API response data.

        Args:
            data (dict): A dictionary containing auction data from the API.

        Returns:
            Auction: An Auction instance populated with the provided data.
        """
        return cls(**data)

    def model_dump(self, **kwargs):
        """Generates a dictionary representation of the auction.

        Returns:
            dict: Dictionary representation of the auction, excluding
            the 'cluster_id' key.
        """
        data = super().model_dump(**kwargs)
        data.pop("cluster_id", None)
        return data

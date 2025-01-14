"""BidManager module that handles bid payload preparation and submission."""

from typing import List, Optional
import logging

from flow.clients.foundry_client import FoundryClient
from flow.logging.spinner_logger import SpinnerLogger
from flow.models import Bid, BidDiskAttachment, BidPayload, DiskAttachment
from pydantic import ValidationError


class BidManager:
    """Manages bid payloads and submission to the Foundry API."""

    def __init__(self, foundry_client: FoundryClient):
        """Initializes the BidManager with the given FoundryClient.

        Args:
            foundry_client: An instance of FoundryClient to interact with
                the Foundry API.
        """
        self.foundry_client = foundry_client
        self.logger = logging.getLogger(__name__)
        self.spinner_logger = SpinnerLogger(self.logger)

    def prepare_bid_payload(
        self,
        *,
        cluster_id: str,
        instance_quantity: int,
        instance_type_id: str,
        limit_price_cents: int,
        order_name: str,
        project_id: str,
        ssh_key_id: str,
        user_id: str,
        startup_script: Optional[str] = None,
        disk_attachments: Optional[List[DiskAttachment]] = None,
    ) -> BidPayload:
        """Prepares and validates the bid payload using Pydantic models.

        Args:
            cluster_id: The ID of the cluster.
            instance_quantity: The number of instances.
            instance_type_id: The type ID of the instance.
            limit_price_cents: The limit price in cents.
            order_name: The name of the bid.
            project_id: The ID of the project.
            ssh_key_id: The SSH key ID.
            user_id: The user ID.
            startup_script: The startup script.
            disk_attachments: Optional list of disk attachments.

        Returns:
            A validated BidPayload model instance.

        Raises:
            ValidationError: If the payload does not match expected schema.
        """
        try:
            bid_disk_attachments = []
            if disk_attachments:
                bid_disk_attachments = [
                    BidDiskAttachment.from_disk_attachment(da)
                    for da in disk_attachments
                ]

            bid_payload = BidPayload(
                cluster_id=cluster_id,
                instance_quantity=instance_quantity,
                instance_type_id=instance_type_id,
                limit_price_cents=limit_price_cents,
                order_name=order_name,
                project_id=project_id,
                ssh_key_ids=[ssh_key_id],
                user_id=user_id,
                startup_script=startup_script,
                disk_attachments=bid_disk_attachments,
            )
            return bid_payload
        except ValidationError as err:
            raise err

    def submit_bid(self, *, project_id: str, bid_payload: BidPayload) -> Bid:
        """Submits a bid to the FoundryClient.

        Args:
            project_id: The identifier of the project.
            bid_payload: The BidPayload object to submit.

        Returns:
            The Bid object returned by the FoundryClient.
        """
        self.logger.info("Submitting bid via FoundryClient...")
        response_bid = self.foundry_client.place_bid(
            project_id=project_id,
            bid_payload=bid_payload,
        )
        self.logger.info("Bid submitted successfully!")
        return response_bid

    def get_bids(self, *, project_id: str) -> List[Bid]:
        """Retrieves all bids for a specified project.

        Args:
            project_id: The identifier of the project.

        Returns:
            A list of Bid objects.
        """
        return self.foundry_client.get_bids(project_id=project_id)

    def cancel_bid(self, *, project_id: str, bid_id: str) -> None:
        """Cancels a bid by ID.

        Args:
            project_id: The identifier of the project.
            bid_id: The identifier of the bid to cancel.
        """
        self.foundry_client.cancel_bid(project_id=project_id, bid_id=bid_id)

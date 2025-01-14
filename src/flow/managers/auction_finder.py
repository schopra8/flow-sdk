import re
from typing import List

from flow.clients.foundry_client import FoundryClient
from flow.models import Auction
from flow.task_config.config_parser import ResourcesSpecification
from flow.logging.spinner_logger import SpinnerLogger


class AuctionFinder:
    """Provides methods to find auctions matching specified criteria."""

    def __init__(self, foundry_client: FoundryClient):
        """Initialize an AuctionFinder instance.

        Args:
            foundry_client: The Foundry client to fetch auctions.
        """
        self.foundry_client = foundry_client
        self.logger = (
            foundry_client.logger if hasattr(foundry_client, "logger") else None
        )
        if not self.logger:
            import logging

            self.logger = logging.getLogger(__name__)
        self.spinner_logger = SpinnerLogger(self.logger)

    def fetch_auctions(self, project_id: str) -> List[Auction]:
        """Fetch auctions for a given project ID.

        Args:
            project_id: The project ID to fetch auctions for.

        Returns:
            A list of Auction objects.
        """
        self.logger.info("Fetching auctions for project ID %s...", project_id)
        auctions = self.foundry_client.get_auctions(project_id=project_id)
        self.logger.info("Fetched %d auctions.", len(auctions))
        return auctions

    def find_matching_auctions(
        self, auctions: List[Auction], criteria: ResourcesSpecification
    ) -> List[Auction]:
        """Find auctions that match the specified criteria.

        Args:
            auctions: A list of Auction objects to search.
            criteria: The ResourcesSpecification to match against.

        Returns:
            A list of Auction objects that match the criteria.
        """
        matching_auctions = []
        for auction in auctions:
            if self._matches_criteria(auction=auction, criteria=criteria):
                matching_auctions.append(auction)
        return matching_auctions

    def _matches_criteria(
        self, auction: Auction, criteria: ResourcesSpecification
    ) -> bool:
        """Check if an auction matches the provided criteria.

        Args:
            auction: The Auction object to check.
            criteria: The ResourcesSpecification to compare against.

        Returns:
            True if the auction meets the criteria, False otherwise.
        """
        # Match GPU type
        if criteria.gpu_type:
            expected_gpu_type = criteria.gpu_type.lower()
            actual_gpu_type = (auction.gpu_type or "").lower()
            pattern = r"\b" + re.escape(expected_gpu_type) + r"\b"
            if not re.search(pattern, actual_gpu_type):
                return False

        # Match number of GPUs
        if criteria.num_gpus is not None:
            expected_num_gpus = criteria.num_gpus
            actual_num_gpus = auction.inventory_quantity
            if (actual_num_gpus is None) or (actual_num_gpus < expected_num_gpus):
                return False

        # TODO(jaredquincy): Add these to the spec so we can filter on this
        # Match internode interconnect
        if criteria.internode_interconnect:
            expected = criteria.internode_interconnect.lower()
            actual = (auction.internode_interconnect or "").lower()
            if expected != actual:
                return False

        # Match intranode interconnect
        if criteria.intranode_interconnect:
            expected = criteria.intranode_interconnect.lower()
            actual = (auction.intranode_interconnect or "").lower()
            if expected != actual:
                return False

        return True

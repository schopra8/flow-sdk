import logging
from typing import Dict, List

from flow.clients.authenticator import Authenticator
from flow.clients.fcp_client import FCPClient
from flow.clients.storage_client import StorageClient
from flow.utils.exceptions import APIError
from flow.models import (
    User,
    Project,
    Instance,
    Auction,
    SshKey,
    Bid,
    BidPayload,
    BidResponse,
    DetailedInstanceType,
    DiskAttachment,
    DiskResponse,
    RegionResponse,
    StorageQuotaResponse,
)


class FoundryClient:
    """
    A high-level client for interacting with the Foundry Cloud Platform (FCP).
    Provides convenience methods to manage projects, instances, bids, storage
    resources, etc. under a single interface.

    Usage Example:
        client = FoundryClient(email="user@example.com", password="secret")
        user = client.get_user()
        projects = client.get_projects()
    """

    def __init__(self, email: str, password: str) -> None:
        """
        Initialize FoundryClient with user credentials. This sets up
        Authenticator, FCPClient, and StorageClient instances.

        Args:
            email: User's email address for authentication.
            password: User's password for authentication.
        """
        self._logger = logging.getLogger(__name__)
        self._logger.debug("Initializing FoundryClient with email=%s", email)

        self._authenticator = Authenticator(email=email, password=password)
        self.fcp_client = FCPClient(authenticator=self._authenticator)
        self.storage_client = StorageClient(authenticator=self._authenticator)

        self._logger.info("FoundryClient initialized successfully")

    # ----------------------------------------------------------------------
    #                        FCPClient Methods
    # ----------------------------------------------------------------------

    def get_user(self) -> User:
        """
        Retrieve the currently authenticated user's information.

        Returns:
            A User model containing the user's profile details.
        """
        self._logger.debug("Retrieving user information via FCPClient.")
        return self.fcp_client.get_user()

    def get_projects(self) -> List[Project]:
        """
        Retrieve a list of all accessible projects for the authenticated user.

        Returns:
            A list of Project models.
        """
        self._logger.debug("Fetching projects from FCPClient.")
        return self.fcp_client.get_projects()

    def get_project_by_name(self, project_name: str) -> Project:
        """
        Retrieve a project by its name.

        Args:
            project_name: The name of the project to locate.

        Returns:
            A matching Project model.

        Raises:
            ValueError: If no matching project is found.
        """
        self._logger.debug("Looking up project by name=%s", project_name)
        return self.fcp_client.get_project_by_name(project_name=project_name)

    def get_instances(self, project_id: str) -> Dict[str, List[Instance]]:
        """
        Retrieve instances within a project, organized by category (e.g., "spot", "reserved").

        Args:
            project_id: The project ID for which to retrieve instances.

        Returns:
            A dict mapping category strings to lists of Instance objects.
        """
        self._logger.debug("Fetching instances for project_id=%s", project_id)
        return self.fcp_client.get_instances(project_id=project_id)

    def get_auctions(self, project_id: str) -> List[Auction]:
        """
        Fetch auctions for a specified project.

        Args:
            project_id: The ID of the project.

        Returns:
            A list of Auction models.

        Raises:
            Exception: If retrieval fails for any reason (e.g., network, parsing).
        """
        self._logger.debug("Fetching auctions for project_id=%s", project_id)
        try:
            auctions = self.fcp_client.get_auctions(project_id=project_id)
            self._logger.debug("Successfully retrieved %d auctions.", len(auctions))
            return auctions
        except Exception as exc:
            self._logger.error(
                "Failed to fetch auctions for project_id=%s: %s", project_id, exc
            )
            raise

    def get_ssh_keys(self, project_id: str) -> List[SshKey]:
        """
        Retrieve SSH keys associated with the specified project.

        Args:
            project_id: The ID of the project.

        Returns:
            A list of SSHKey models.
        """
        self._logger.debug("Fetching SSH keys for project_id=%s", project_id)
        return self.fcp_client.get_ssh_keys(project_id=project_id)

    def get_bids(self, project_id: str) -> List[Bid]:
        """
        Retrieve all bids for a given project.

        Args:
            project_id: The ID of the project.

        Returns:
            A list of Bid models.
        """
        self._logger.debug("Fetching bids for project_id=%s", project_id)
        return self.fcp_client.get_bids(project_id=project_id)

    def place_bid(self, project_id: str, bid_payload: BidPayload) -> BidResponse:
        """
        Place a bid on a specified project.

        Args:
            project_id: The ID of the project where the bid is placed.
            bid_payload: BidPayload with bid details (excluding project_id).

        Returns:
            A BidResponse model with details of the placed bid.

        Raises:
            Exception: For any network/validation errors during bid placement.
        """
        self._logger.debug(
            "Placing bid on project_id=%s with payload=%s",
            project_id,
            bid_payload.model_dump(),
        )
        try:
            updated_payload = bid_payload.model_copy(update={"project_id": project_id})
            bid_response = self.fcp_client.place_bid(updated_payload)
            self._logger.debug(
                "Bid placed successfully. Response=%s", bid_response.model_dump()
            )
            return bid_response
        except Exception as exc:
            self._logger.error(
                "Error placing bid on project_id=%s: %s", project_id, exc, exc_info=True
            )
            raise

    def cancel_bid(self, project_id: str, bid_id: str) -> None:
        """
        Cancel an existing bid in a project.

        Args:
            project_id: The project's ID where the bid was placed.
            bid_id: The ID of the bid to cancel.
        """
        self._logger.debug("Canceling bid_id=%s for project_id=%s", bid_id, project_id)
        self.fcp_client.cancel_bid(project_id=project_id, bid_id=bid_id)
        self._logger.info(
            "Canceled bid_id=%s in project_id=%s successfully.", bid_id, project_id
        )

    def get_instance_type(self, instance_type_id: str) -> DetailedInstanceType:
        """
        Retrieve details for a specified instance type.

        If the instance type is not found (404), a fallback DetailedInstanceType
        is returned rather than raising an exception.

        Args:
            instance_type_id: The ID of the instance type to look up.

        Returns:
            A DetailedInstanceType model with the instance type's information.
            If not found, a fallback object is returned.

        Raises:
            APIError: For non-404 errors.
        """
        self._logger.debug("Fetching instance type for id=%s", instance_type_id)
        try:
            response = self.fcp_client._request(
                method="GET",
                path=f"/instance_types/{instance_type_id}",
            )
            data = response.json()
            self._logger.info(
                "Retrieved instance_type data for %s: %s", instance_type_id, data
            )
            return DetailedInstanceType(**data)
        except APIError as err:
            not_found = "404" in str(err) or (
                hasattr(err, "response")
                and err.response is not None
                and err.response.status_code == 404
            )
            if not_found:
                self._logger.warning(
                    "InstanceType id=%s not found, returning fallback.",
                    instance_type_id,
                )
                return DetailedInstanceType(
                    id=instance_type_id,
                    name="[Unknown / Not Found]",
                    num_cpus=None,
                    num_gpus=None,
                    memory_gb=None,
                    architecture=None,
                )

            self._logger.error(
                "Failed to retrieve instance_type id=%s due to APIError: %s",
                instance_type_id,
                err,
            )
            raise

    # ----------------------------------------------------------------------
    #                      StorageClient Methods
    # ----------------------------------------------------------------------

    def create_disk(
        self, project_id: str, disk_attachment: DiskAttachment
    ) -> DiskResponse:
        """
        Create a new disk in the specified project.

        Args:
            project_id: The project ID.
            disk_attachment: DiskAttachment model with disk setup details.

        Returns:
            A DiskResponse model with details of the newly created disk.
        """
        self._logger.debug(
            "Creating disk in project_id=%s with disk_id=%s",
            project_id,
            disk_attachment.disk_id,
        )
        disk_response = self.storage_client.create_disk(
            project_id=project_id,
            disk_attachment=disk_attachment,
        )
        self._logger.debug("Created disk successfully: %s", disk_response.model_dump())
        return disk_response

    def get_disks(self, project_id: str) -> List[DiskResponse]:
        """
        Retrieve all disks in a given project.

        Args:
            project_id: The ID of the project.

        Returns:
            A list of DiskResponse models.
        """
        self._logger.debug("Fetching disks for project_id=%s", project_id)
        disks = self.storage_client.get_disks(project_id=project_id)
        self._logger.debug("Retrieved %d disks.", len(disks))
        return disks

    def delete_disk(self, project_id: str, disk_id: str) -> None:
        """
        Delete a disk from a given project.

        Args:
            project_id: The ID of the project.
            disk_id: The ID of the disk to delete.
        """
        self._logger.debug(
            "Deleting disk_id=%s from project_id=%s", disk_id, project_id
        )
        self.storage_client.delete_disk(project_id=project_id, disk_id=disk_id)
        self._logger.info(
            "Deleted disk_id=%s from project_id=%s successfully.", disk_id, project_id
        )

    def get_storage_quota(self, project_id: str) -> StorageQuotaResponse:
        """
        Retrieve the storage quota for a specific project.

        Args:
            project_id: The project ID.

        Returns:
            A StorageQuotaResponse model.
        """
        self._logger.debug("Fetching storage quota for project_id=%s", project_id)
        quota = self.storage_client.get_storage_quota(project_id=project_id)
        self._logger.debug("Retrieved storage quota: %s", quota.model_dump())
        return quota

    def get_regions(self) -> List[RegionResponse]:
        """
        Retrieve all available regions from the Foundry platform.

        Returns:
            A list of RegionResponse models.

        Raises:
            Exception: If fetching regions fails.
        """
        self._logger.debug("Fetching all regions from StorageClient.")
        try:
            regions = self.storage_client.get_regions()
            self._logger.debug("Retrieved %d region(s).", len(regions))
            return regions
        except Exception as exc:
            self._logger.error("Failed to retrieve regions: %s", exc, exc_info=True)
            raise

    def get_disk(self, project_id: str, disk_id: str) -> DiskResponse:
        """
        Retrieve information about a given disk in a specific project.

        Args:
            project_id: The project ID.
            disk_id: The disk ID.

        Returns:
            A DiskResponse model of the requested disk.
        """
        self._logger.debug("Fetching disk_id=%s in project_id=%s", disk_id, project_id)
        disk_info = self.storage_client.get_disk(project_id=project_id, disk_id=disk_id)
        self._logger.debug("Fetched disk info: %s", disk_info.model_dump())
        return disk_info

    def get_region_id_by_name(self, region_name: str) -> str:
        """
        Look up a region's UUID by its human-friendly name (e.g., 'us-central1-a').

        Args:
            region_name: The name of the region to look up.

        Returns:
            The corresponding region_id (UUID string).

        Raises:
            ValueError: If no matching region name is found.
        """
        self._logger.debug("Looking up region ID for region_name='%s'", region_name)
        all_regions = self.get_regions()
        self._logger.debug("Retrieved %d region(s) total.", len(all_regions))

        for region_response in all_regions:
            self._logger.debug(
                "Examining region '%s' (id=%s)",
                region_response.name,
                region_response.region_id,
            )
            if region_response.name == region_name:
                self._logger.debug(
                    "Matched region_name='%s' -> region_id='%s'",
                    region_name,
                    region_response.region_id,
                )
                return region_response.region_id

        self._logger.warning("No matching region found for name='%s'", region_name)
        raise ValueError(f"Region not found for name='{region_name}'")

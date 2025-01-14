"""
Integration tests for the StorageClient class, focusing on disk lifecycle.
These tests also require environment variables (FOUNDRY_EMAIL, FOUNDRY_PASSWORD, and FOUNDRY_PROJECT_NAME).
We explicitly skip if they are missing, and never log their values for security.
"""

import logging
import os
import sys
import unittest
import uuid
from typing import List

from pydantic import ValidationError
import pytest

# Insert src directory if needed.
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src"))
)

from flow.clients.authenticator import Authenticator
from flow.clients.fcp_client import FCPClient
from flow.clients.storage_client import StorageClient
from flow.models.disk_attachment import DiskAttachment
from flow.models.storage_responses import (
    DiskResponse,
    RegionResponse,
    StorageQuotaResponse,
)
from flow.utils.exceptions import (
    APIError,
    AuthenticationError,
    InvalidResponseError,
    NetworkError,
)

# Environment variable keys.
_ENV_EMAIL = "FOUNDRY_EMAIL"
_ENV_PASSWORD = "FOUNDRY_PASSWORD"
_ENV_PROJECT_ID = "FOUNDRY_PROJECT_NAME"


@pytest.mark.skipif(
    not (
        os.getenv(_ENV_EMAIL)
        and os.getenv(_ENV_PASSWORD)
        and os.getenv(_ENV_PROJECT_ID)
    ),
    reason="Missing environment variables necessary for StorageClientIntegrationTest",
)
class StorageClientIntegrationTest(unittest.TestCase):
    """Integration tests for StorageClient interactions with the live API.

    Covers disk lifecycle (create, list, delete) and storage quota queries.
    """

    @classmethod
    def setUpClass(cls):
        """Prepares test environment and resources before any tests run.

        Steps:
          - Validates environment variables.
          - Initializes StorageClient and stores it in cls._storage_client.
          - Retrieves a valid region_id and stores it.
        """
        cls._email = os.getenv(_ENV_EMAIL)
        cls._password = os.getenv(_ENV_PASSWORD)
        cls._project_id = os.getenv(_ENV_PROJECT_ID)

        missing_vars = []
        if not cls._email:
            missing_vars.append(_ENV_EMAIL)
        if not cls._password:
            missing_vars.append(_ENV_PASSWORD)
        if not cls._project_id:
            missing_vars.append(_ENV_PROJECT_ID)

        if missing_vars:
            raise EnvironmentError(
                f"Missing environment variables: {', '.join(missing_vars)}"
            )

        try:
            authenticator = Authenticator(email=cls._email, password=cls._password)
            cls._storage_client = StorageClient(authenticator=authenticator)
        except (AuthenticationError, NetworkError) as err:
            raise RuntimeError(f"Failed to initialize StorageClient: {err}")

        try:
            fcp_client = FCPClient(authenticator=authenticator)
            foundry_project = fcp_client.get_project_by_name(
                project_name=cls._project_id
            )
            cls._project_id = foundry_project.id
        except (APIError, AuthenticationError, NetworkError) as err:
            raise RuntimeError(f"Failed to resolve project by name: {err}")

        try:
            regions: List[RegionResponse] = cls._storage_client.get_regions()
            if not regions:
                raise ValueError("No regions available.")
            cls._region_id = regions[0].region_id
        except (
            APIError,
            AuthenticationError,
            NetworkError,
            InvalidResponseError,
            ValueError,
        ) as err:
            raise RuntimeError(f"Failed to retrieve regions: {err}")

        cls._disks_to_cleanup = []

    @classmethod
    def tearDownClass(cls):
        """Cleans up resources (e.g., disks) after all tests have run."""
        for disk_info in cls._disks_to_cleanup:
            project_id = disk_info["project_id"]
            disk_id = disk_info["disk_id"]
            try:
                logging.debug("Cleaning up disk with ID: %s", disk_id)
                cls._storage_client.delete_disk(project_id=project_id, disk_id=disk_id)
                logging.debug("Successfully cleaned up disk: %s", disk_id)
            except Exception as err:  # pylint: disable=broad-except
                logging.error(
                    "Failed to delete disk '%s' during cleanup: %s", disk_id, err
                )

    def setUp(self):
        """Prepares resources before each individual test.

        Steps:
          - Generates a unique disk ID and name.
        """
        self._disk_id = str(uuid.uuid4())
        self._disk_name = f"testdisk-{uuid.uuid4().hex}"
        self._disk_interface = "Block"
        self._size = 1  # in GB
        self._size_unit = "gb"
        self._project_id = self.__class__._project_id
        self._created_disk_id = None

    def test_create_get_delete_disk(self):
        """Tests creating, retrieving, and deleting a disk."""
        logging.debug("Starting test: test_create_get_delete_disk")

        # Create the disk (returns a DiskResponse).
        created_disk = self._create_disk()
        self.assertIsInstance(created_disk, DiskResponse)
        self.assertEqual(created_disk.disk_id, self._disk_id)
        self.assertEqual(created_disk.name, self._disk_name)
        self._created_disk_id = created_disk.disk_id

        # Retrieve disks and check if the created disk is present.
        disks = self._get_disks()
        self.assertIsInstance(disks, list)
        disk_ids = [disk.disk_id for disk in disks]
        logging.debug("List of disk IDs retrieved: %s", disk_ids)
        self.assertIn(self._created_disk_id, disk_ids)

        # Delete the disk.
        self._delete_disk()

        # Verify the disk is no longer present.
        disks = self._get_disks()
        disk_ids = [disk.disk_id for disk in disks]
        logging.debug("List of disk IDs after deletion: %s", disk_ids)
        self.assertNotIn(self._created_disk_id, disk_ids)
        logging.debug("Completed test: test_create_get_delete_disk")

    def test_get_storage_quota(self):
        """Tests retrieving storage quota for a project."""
        logging.debug("Starting test: test_get_storage_quota")
        try:
            quota = self._storage_client.get_storage_quota(project_id=self._project_id)
            self.assertIsInstance(
                quota,
                StorageQuotaResponse,
                "Quota response should be a StorageQuotaResponse.",
            )
            self.assertGreaterEqual(quota.total_storage, 0)
            self.assertGreaterEqual(quota.used_storage, 0)
            logging.debug("Retrieved storage quota: %s", quota)
        except (
            APIError,
            AuthenticationError,
            NetworkError,
            InvalidResponseError,
        ) as err:
            self.fail(f"Exception occurred during get_storage_quota: {err}")

    def _create_disk(self) -> DiskResponse:
        """Creates a disk for test usage.

        Returns:
            A DiskResponse instance representing the created disk.
        Raises:
            Test failure if any known exception is raised during disk creation.
        """
        try:
            logging.debug("Creating disk with ID: %s", self._disk_id)
            disk_attachment = DiskAttachment(
                name=self._disk_name,
                disk_id=self._disk_id,
                disk_interface=self._disk_interface,
                region_id=self.__class__._region_id,
                size=self._size,
                size_unit=self._size_unit,
            )
            response = self._storage_client.create_disk(
                project_id=self._project_id,
                disk_attachment=disk_attachment,
            )
            self.assertIsInstance(response, DiskResponse)
            self.__class__._disks_to_cleanup.append(
                {"project_id": self._project_id, "disk_id": response.disk_id}
            )
            logging.debug("Create Disk Response: %s", response)
            return response
        except (
            APIError,
            AuthenticationError,
            NetworkError,
            InvalidResponseError,
            ValidationError,
        ) as err:
            self.fail(f"Exception occurred during disk creation: {err}")

    def _get_disks(self) -> List[DiskResponse]:
        """Retrieves a list of disks from the StorageClient.

        Returns:
            A list of DiskResponse objects representing currently available disks.
        Raises:
            Test failure if any known exception is raised during disk retrieval.
        """
        try:
            disks = self._storage_client.get_disks(project_id=self._project_id)
            self.assertIsInstance(disks, list)
            for disk in disks:
                self.assertIsInstance(disk, DiskResponse)
            logging.debug("Retrieved Disks: %s", disks)
            return disks
        except (
            APIError,
            AuthenticationError,
            NetworkError,
            InvalidResponseError,
            ValueError,
        ) as err:
            self.fail(f"Exception occurred during retrieving disks: {err}")

    def _delete_disk(self):
        """Deletes a previously created disk."""
        if not self._created_disk_id:
            self.fail("No disk created before calling _delete_disk.")
        try:
            logging.debug("Deleting disk with ID: %s", self._created_disk_id)
            self._storage_client.delete_disk(
                project_id=self._project_id, disk_id=self._created_disk_id
            )
            self.__class__._disks_to_cleanup = [
                disk
                for disk in self.__class__._disks_to_cleanup
                if disk["disk_id"] != self._created_disk_id
            ]
            logging.debug("Deleted disk with ID: %s", self._created_disk_id)
        except (
            APIError,
            AuthenticationError,
            NetworkError,
            InvalidResponseError,
            ValueError,
        ) as err:
            self.fail(f"Exception occurred during disk deletion: {err}")

    @classmethod
    def tearDownClass(cls):
        """Cleans up resources after all tests have run."""
        for disk in cls._disks_to_cleanup:
            try:
                logging.debug("Cleaning up disk with ID: %s", disk["disk_id"])
                cls._storage_client.delete_disk(
                    project_id=disk["project_id"], disk_id=disk["disk_id"]
                )
                logging.debug(
                    "Successfully cleaned up disk with ID: %s", disk["disk_id"]
                )
            except Exception as err:  # pylint: disable=broad-except
                logging.error(
                    "Failed to delete disk '%s' during cleanup: %s",
                    disk["disk_id"],
                    err,
                )


if __name__ == "__main__":
    unittest.main()

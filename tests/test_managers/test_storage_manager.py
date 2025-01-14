"""Comprehensive unit tests for the StorageManager class.

These tests ensure correct handling of persistent storage creation and region
fetching, verifying expected behavior and error-handling paths.
"""

import uuid
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from flow.task_config import PersistentStorage
from flow.managers.storage_manager import StorageManager
from flow.models import DiskAttachment
from flow.utils.exceptions import APIError


@pytest.fixture
def mock_foundry_client():
    """Returns a mock of FoundryClient usable in StorageManager tests."""
    return MagicMock()


@pytest.fixture
def storage_manager(mock_foundry_client):
    """Returns a StorageManager instance with a mock FoundryClient."""
    return StorageManager(foundry_client=mock_foundry_client)


@pytest.fixture
def valid_persistent_storage_config() -> PersistentStorage:
    """Returns a valid PersistentStorage creation configuration."""
    return PersistentStorage(
        create={
            "volume_name": "test-volume",
            "disk_interface": "Block",
            "region_id": "test-region",
            "size": 10,
            "size_unit": "gb",
        }
    )


class TestStorageManagerUnit:
    """Unit tests for the StorageManager class."""

    def test_handle_persistent_storage_no_create_config(
        self, storage_manager: StorageManager
    ):
        """Tests None is returned if 'create' is not set in persistent_storage."""
        persistent_storage = PersistentStorage(create=None)
        result = storage_manager.handle_persistent_storage(
            project_id="dummy_project", persistent_storage=persistent_storage
        )
        assert result is None, (
            "handle_persistent_storage should return None when there's no "
            "'create' config."
        )

    def test_handle_persistent_storage_missing_volume_name(
        self, storage_manager: StorageManager
    ):
        """Raises ValueError if 'volume_name' is missing in the creation config."""
        persistent_storage = PersistentStorage(
            create={
                "disk_interface": "Block",
                "region_id": "test-region",
                "size": 10,
            }
        )
        with pytest.raises(ValueError, match="Volume name must be specified"):
            storage_manager.handle_persistent_storage(
                "dummy_project", persistent_storage
            )

    def test_handle_persistent_storage_missing_size(
        self, storage_manager: StorageManager
    ):
        """Raises ValueError if 'size' is missing in the creation config."""
        persistent_storage = PersistentStorage(
            create={
                "volume_name": "test-volume",
                "disk_interface": "Block",
                "region_id": "test-region",
            }
        )
        with pytest.raises(ValueError, match="Disk size must be specified"):
            storage_manager.handle_persistent_storage(
                "dummy_project", persistent_storage
            )

    @patch("uuid.uuid4")
    def test_handle_persistent_storage_creation_success(
        self,
        mock_uuid,
        storage_manager: StorageManager,
        valid_persistent_storage_config: PersistentStorage,
    ):
        """Tests disk creation success with mocked Foundry client."""
        mock_uuid.side_effect = [
            uuid.UUID(hex="abcd1234abcd1234abcd1234abcd1234"),
            uuid.UUID(hex="dcba4321dcba4321dcba4321dcba4321"),
        ]

        mock_region = MagicMock()
        mock_region.region_id = "some-region-id"
        mock_region.name = "test-region"
        storage_manager.foundry_client.get_regions.return_value = [mock_region]

        storage_manager.foundry_client.create_disk.return_value = MagicMock(
            disk_id="created-disk-id"
        )

        result = storage_manager.handle_persistent_storage(
            project_id="dummy_project",
            persistent_storage=valid_persistent_storage_config,
        )

        storage_manager.foundry_client.create_disk.assert_called_once()
        assert isinstance(result, DiskAttachment)
        assert result.disk_id == "created-disk-id"
        assert result.volume_name.startswith("test-volume-")
        assert result.region_id == "some-region-id"

    @patch("uuid.uuid4")
    def test_handle_persistent_storage_creation_api_failure(
        self,
        mock_uuid,
        storage_manager: StorageManager,
        valid_persistent_storage_config: PersistentStorage,
    ):
        """Tests APIError handling when the FoundryClient fails to create a disk."""
        mock_uuid.return_value = uuid.UUID(hex="abcd1234abcd1234abcd1234abcd1234")

        mock_region = MagicMock()
        mock_region.region_id = "some-region-id"
        mock_region.name = "test-region"
        storage_manager.foundry_client.get_regions.return_value = [mock_region]

        storage_manager.foundry_client.create_disk.side_effect = APIError(
            "Test API failure"
        )

        with pytest.raises(APIError, match="Failed to create disk"):
            storage_manager.handle_persistent_storage(
                project_id="dummy_project",
                persistent_storage=valid_persistent_storage_config,
            )

    def test_handle_persistent_storage_inherited_default_region(
        self, storage_manager: StorageManager
    ):
        """Tests that the default region is used if no region is supplied."""
        storage_manager.get_default_region_id = MagicMock(
            return_value="fallback-region"
        )

        persistent_storage = PersistentStorage(
            create={
                "volume_name": "test-volume",
                "disk_interface": "Block",
                "size": 10,
                "region_id": None,
            }
        )

        storage_manager.foundry_client.create_disk.return_value = MagicMock(
            disk_id="test-id"
        )

        result = storage_manager.handle_persistent_storage(
            project_id="dummy_project", persistent_storage=persistent_storage
        )

        assert result is not None
        assert result.region_id == "fallback-region"

    def test_get_default_region_id_no_regions(self, storage_manager: StorageManager):
        """Tests that an exception is raised if there are no available regions."""
        storage_manager.foundry_client.get_regions.return_value = []
        with pytest.raises(Exception, match="No regions available"):
            storage_manager.get_default_region_id()

    def test_get_default_region_id_success(self, storage_manager: StorageManager):
        """Tests that the first region_id in the get_regions response is returned."""
        mock_region = MagicMock()
        mock_region.region_id = "us-central1-a"
        mock_region.name = "some-region-name"
        storage_manager.foundry_client.get_regions.return_value = [mock_region]

        region_id = storage_manager.get_default_region_id()
        assert region_id == "us-central1-a", f"Unexpected region_id: {region_id}"
        storage_manager.foundry_client.get_regions.assert_called_once()

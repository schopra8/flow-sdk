import logging
import unittest
import warnings
from unittest.mock import Mock

from flow.clients.foundry_client import FoundryClient
from flow.managers.instance_manager import InstanceManager
from flow.models import Instance, ReservedInstance, SpotInstance


class TestInstanceManager(unittest.TestCase):
    """Tests for the InstanceManager class."""

    @classmethod
    def setUpClass(cls):
        """Sets up the class by ignoring pydantic's `json_encoders` deprecation warnings."""
        super().setUpClass()
        warnings.filterwarnings(
            "ignore",
            message=r".*`json_encoders` is deprecated.*",
            category=DeprecationWarning,
        )
        logging.getLogger(__name__).info(
            "Ignoring pydantic's `json_encoders` deprecation warnings in tests."
        )

    def setUp(self):
        """Sets up the test case with a mock FoundryClient and InstanceManager."""
        self.foundry_client = Mock(spec=FoundryClient)
        self.instance_manager = InstanceManager(self.foundry_client)

    def test_get_instances(self):
        """Tests retrieving and parsing instances."""
        mock_instances_response = {
            "spot": [
                {
                    "instance_id": "inst-123",
                    "name": "spot-instance",
                    "instance_status": "running",
                    "instance_type_id": "type-1",
                    "start_date": "2023-11-10T12:34:56Z",
                    "connection_info": {"ip_address": "192.168.1.10"},
                }
            ],
            "reserved": [
                {
                    "instance_id": "inst-456",
                    "name": "reserved-instance",
                    "instance_status": "stopped",
                    "instance_type_id": "type-2",
                    "start_date": "2023-11-09T08:00:00Z",
                    "connection_info": {"ip_address": "192.168.1.20"},
                }
            ],
        }
        # Mock FoundryClient.get_instances to return the mock response.
        self.foundry_client.get_instances.return_value = mock_instances_response

        instances = self.instance_manager.get_instances("proj-123")
        self.assertEqual(len(instances), 2, "Should have 2 flattened instances")

        # Check the first instance.
        self.assertIsInstance(instances[0], SpotInstance)
        self.assertEqual(instances[0].category, "spot")
        self.assertEqual(instances[0].name, "spot-instance")
        self.assertEqual(instances[0].ip_address, "192.168.1.10")

        # Check the second instance.
        self.assertIsInstance(instances[1], ReservedInstance)
        self.assertEqual(instances[1].category, "reserved")
        self.assertEqual(instances[1].name, "reserved-instance")
        self.assertEqual(instances[1].ip_address, "192.168.1.20")

    def test_create_instance_from_unknown_category(self):
        """Tests creating an instance with an unknown category."""
        data = {
            "instance_id": "inst-789",
            "name": "unknown-instance",
            "instance_status": "pending",
            "instance_type_id": "type-3",
            "start_date": "2023-11-11T09:00:00Z",
            "connection_info": {"ip_address": "192.168.1.30"},
        }

        with self.assertLogs("InstanceManager", level="WARNING") as captured:
            instance = self.instance_manager._create_instance_from_dict(data, "unknown")

        self.assertTrue(
            any(
                "Unknown instance category 'unknown'" in message
                for message in captured.output
            ),
            "Should log a warning about unknown category",
        )
        self.assertIsInstance(instance, Instance)
        self.assertEqual(instance.category, "unknown")
        self.assertEqual(instance.name, "unknown-instance")
        self.assertEqual(instance.ip_address, "192.168.1.30")


if __name__ == "__main__":
    unittest.main()

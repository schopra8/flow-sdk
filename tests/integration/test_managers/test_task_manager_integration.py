import json
import logging
import os
import random
import string
import unittest
import uuid
import time

import pytest
import yaml

from src.flow.config import get_config
from src.flow.task_config import ConfigParser
from src.flow.clients.foundry_client import FoundryClient
from src.flow.managers.auction_finder import AuctionFinder
from src.flow.managers.bid_manager import BidManager
from src.flow.managers.storage_manager import StorageManager
from src.flow.managers.task_manager import FlowTaskManager
settings = get_config()

TEST_YAML_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../flow_example.yaml"))

@pytest.mark.skipif(
    not all(
        [
            settings.foundry_email,
            bool(settings.foundry_password.get_secret_value().strip()),
            settings.foundry_project_name,
            settings.foundry_ssh_key_name,
        ]
    ),
    reason="Skipping FlowTaskManagerIntegration tests due to missing required environment variables.",
)
class TestFlowTaskManagerIntegration(unittest.TestCase):
    """Integration tests for FlowTaskManager, verifying end-to-end functionality."""

    def setUp(self):
        """Set up the integration test environment with real config usage."""
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)

        # Generate a random 3-digit suffix
        self.random_suffix = "".join(random.choices(string.digits, k=3))

        # Load and modify the YAML configuration file
        with open(TEST_YAML_FILE, "r", encoding="utf-8") as file:
            config_data = yaml.safe_load(file)

        original_name = config_data.get("name", "flow-task")
        config_data["name"] = f"{original_name}-test-{self.random_suffix}"
        config_data["resources_specification"] = {
            "fcp_instance": "fh1.xlarge",
            "num_instances": 1,
            "gpu_type": "NVIDIA A100",
            "num_gpus": 1,
        }

        print("\nUsing resource specifications:")
        print(json.dumps(config_data["resources_specification"], indent=2))

        # Generate a truly unique disk name
        timestamp_str = time.strftime("%Y%m%d%H%M%S")
        rand_tail = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
        self.disk_id = str(uuid.uuid4())
        self.disk_name = f"testdisk-{timestamp_str}-{rand_tail}"
        self.disk_interface = "Block"
        self.size = 1
        self.size_unit = "gb"
        self.actual_disk_id = None
        self.disks_to_cleanup = []

        # Update the persistent_storage create config
        if "persistent_storage" not in config_data:
            config_data["persistent_storage"] = {}
        if "create" not in config_data["persistent_storage"]:
            config_data["persistent_storage"]["create"] = {}
        config_data["persistent_storage"]["create"].update(
            {
                "disk_interface": "Block",
                "size": 1,
                "size_unit": "gb",
                # Use our unique self.disk_name
                "volume_name": self.disk_name,
            }
        )

        # Persist the YAML with the updated config
        self.temp_yaml_file = os.path.join(
            os.path.dirname(__file__),
            "temp_test_config.yaml",
        )
        with open(self.temp_yaml_file, "w", encoding="utf-8") as file:
            yaml.dump(config_data, file)

        print(f"Using task name: {config_data['name']}")

        self.config_parser = ConfigParser(filename=self.temp_yaml_file)
        self.foundry_client = FoundryClient(
            email=settings.foundry_email,
            password=settings.foundry_password.get_secret_value(),
        )
        self.auction_finder = AuctionFinder(self.foundry_client)
        self.bid_manager = BidManager(self.foundry_client)

        # Retrieve project ID
        projects = self.foundry_client.get_projects()
        self.project_id = None
        for project in projects:
            if project.name == settings.foundry_project_name:
                self.project_id = project.id
                break
        if not self.project_id:
            self.fail(f"Project '{settings.foundry_project_name}' not found.")

        self.task_manager = FlowTaskManager(
            config_parser=self.config_parser,
            foundry_client=self.foundry_client,
            auction_finder=self.auction_finder,
            bid_manager=self.bid_manager,
        )

        # Initialize storage logic
        self.storage_manager = StorageManager(foundry_client=self.foundry_client)
        print(f"Using disk name: {self.disk_name}")

        # Adjust threshold
        self.config_parser.config.task_management.utility_threshold_price = 600

    def test_create_and_cancel_bid(self):
        """Test creating a bid and then canceling it to ensure end-to-end flow."""
        print("\nRunning integration test: test_create_and_cancel_bid")

        auctions = self.foundry_client.get_auctions(self.project_id)
        print(f"\nAvailable auctions before test ({len(auctions)} total):")
        for auction in auctions:
            print(f"Inspecting auction: {auction.model_dump()}")

        matching_auction = None
        for auction in auctions:
            print(f"Checking auction for match: {auction.model_dump()}")
            if "a100" in (auction.gpu_type or "").lower():
                matching_auction = auction
                print(f"Found matching auction: {matching_auction.model_dump()}")
                break

        if matching_auction:
            self.config_parser.config.resources_specification.num_instances = 1
            self.config_parser.config.resources_specification.gpu_type = matching_auction.gpu_type
            self.config_parser.config.resources_specification.num_gpus = matching_auction.inventory_quantity

            region_val = getattr(matching_auction, "region", None)
            if not region_val:
                self.skipTest("No region found in matching auction. Unable to proceed.")
            print(f"Anchoring storage region to the auction region: {region_val}")

            matching_auction = matching_auction.model_copy(update={"region_id": region_val})
            create_cfg = self.config_parser.config.persistent_storage.create
            self.config_parser.config.persistent_storage.create = create_cfg.model_copy(
                update={"region_id": region_val}
            )

            print("\nUsing resource specifications:")
            print(
                json.dumps(
                    self.config_parser.config.resources_specification.model_dump(),
                    indent=2,
                )
            )
        else:
            print("No suitable auction found for testing.")
            self.skipTest("No suitable auction found for testing")

        timestamp_str = time.strftime("%Y%m%d%H%M%S")
        self.config_parser.config.name = f"flow-test-task-{timestamp_str}"
        print(f"Using random name: {self.config_parser.config.name}")

        self.task_manager.run()

        print("Retrieving projects")
        projects = self.foundry_client.get_projects()
        print(f"Projects retrieved: {projects}")
        project_id = None
        for project in projects:
            print(f"Inspecting project: {project}")
            if project.name == settings.foundry_project_name:
                project_id = project.id
                break
        if not project_id:
            self.fail(f"Project '{settings.foundry_project_name}' not found.")

        print(f"Retrieving bids for project ID: {project_id}")
        bids = self.bid_manager.get_bids(project_id=project_id)
        print(f"Bids retrieved: {bids}")
        self.assertTrue(len(bids) > 0, "No bids found after submission.")

        task_name = self.config_parser.config.name
        print(f"Task name from configuration: {task_name}")

        bid_to_cancel = None
        for bid in bids:
            if hasattr(bid, "name") and bid.name == task_name:
                bid_to_cancel = bid
                print(f"Found bid to cancel: {bid_to_cancel.model_dump()}")
                break

        if not bid_to_cancel:
            self.fail(f"Bid with name '{task_name}' not found after submission.")

        order_name = bid_to_cancel.name
        bid_id = bid_to_cancel.id
        print(f"Order name to cancel: {order_name}")
        print(f"Order ID to cancel: {bid_id}")

        print(f"Cancelling bid with name: {order_name}")
        self.task_manager.cancel_bid(order_name)

        bids_after_cancellation = self.bid_manager.get_bids(project_id=project_id)
        print(f"Bids after cancellation: {bids_after_cancellation}")
        canceled_bid = next((b for b in bids_after_cancellation if b.id == bid_id), None)
        if canceled_bid is None:
            print(f"Bid '{order_name}' has been canceled successfully.")
        else:
            if canceled_bid.status == "canceled" or canceled_bid.deactivated_at:
                print(f"Bid '{order_name}' has been canceled successfully.")
            else:
                self.fail(f"Bid '{order_name}' was not canceled.")

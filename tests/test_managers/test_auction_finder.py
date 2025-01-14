import unittest
from unittest.mock import MagicMock

from flow.managers.auction_finder import AuctionFinder
from flow.clients.foundry_client import FoundryClient
from flow.models import Auction
from flow.task_config.config_parser import ResourcesSpecification


class TestAuctionFinder(unittest.TestCase):
    """Tests for the AuctionFinder class."""

    def setUp(self):
        """Sets up the test case with a mock FoundryClient and sample data."""
        self.mock_foundry_client = MagicMock(spec=FoundryClient)
        self.auction_finder = AuctionFinder(foundry_client=self.mock_foundry_client)
        self.project_id = "test_project_id"
        self.sample_auctions = [
            Auction(
                id="auction1",
                gpu_type="NVIDIA A100",
                inventory_quantity=8,
                intranode_interconnect="SXM",
                internode_interconnect="3200_IB",
            ),
            Auction(
                id="auction2",
                gpu_type="NVIDIA A100",
                inventory_quantity=4,
                intranode_interconnect="PCIe",
                internode_interconnect="1600_IB",
            ),
            Auction(
                id="auction3",
                gpu_type="NVIDIA H100",
                inventory_quantity=8,
                intranode_interconnect="SXM",
                internode_interconnect="3200_IB",
            ),
            Auction(
                id="auction4",
                gpu_type="NVIDIA V100",
                inventory_quantity=16,
                intranode_interconnect="PCIe",
                internode_interconnect="1600_IB",
            ),
        ]

    def test_fetch_auctions_success(self):
        """Tests fetching auctions successfully."""
        self.mock_foundry_client.get_auctions.return_value = [
            auction.model_dump() for auction in self.sample_auctions
        ]

        auctions = self.auction_finder.fetch_auctions(project_id=self.project_id)
        expected_auctions = [auction.model_dump() for auction in self.sample_auctions]
        self.assertEqual(auctions, expected_auctions)

    def test_fetch_auctions_api_failure(self):
        """Tests fetching auctions when the API fails."""
        self.mock_foundry_client.get_auctions.side_effect = Exception("API error")

        with self.assertRaises(Exception) as context:
            self.auction_finder.fetch_auctions(project_id=self.project_id)
        self.assertIn("API error", str(context.exception))

    def test_find_matching_auctions_basic(self):
        """Tests finding matching auctions with basic criteria."""
        criteria = ResourcesSpecification(
            gpu_type="A100",
            num_gpus=4,
        )
        matching_auctions = self.auction_finder.find_matching_auctions(
            auctions=self.sample_auctions,
            criteria=criteria,
        )
        expected_auctions = [self.sample_auctions[0], self.sample_auctions[1]]
        self.assertEqual(matching_auctions, expected_auctions)

    def test_find_matching_auctions_no_matches(self):
        """Tests finding matching auctions when no auctions meet the criteria."""
        criteria = ResourcesSpecification(
            gpu_type="NonExistentGPU",
            num_gpus=999,
        )
        matching_auctions = self.auction_finder.find_matching_auctions(
            auctions=self.sample_auctions,
            criteria=criteria,
        )
        self.assertEqual(matching_auctions, [])

    def test_find_matching_auctions_empty_auctions(self):
        """Tests finding matching auctions when the auction list is empty."""
        criteria = ResourcesSpecification(
            gpu_type="A100",
            num_gpus=4,
        )
        matching_auctions = self.auction_finder.find_matching_auctions(
            auctions=[],
            criteria=criteria,
        )
        self.assertEqual(matching_auctions, [])

    def test_find_matching_auctions_invalid_criteria_values(self):
        """Tests finding matching auctions with invalid criteria values."""
        criteria = ResourcesSpecification(
            gpu_type=None,
            num_gpus=-1,
        )
        matching_auctions = self.auction_finder.find_matching_auctions(
            auctions=self.sample_auctions,
            criteria=criteria,
        )
        self.assertEqual(matching_auctions, self.sample_auctions)

    def test_matches_criteria_all_match(self):
        """Tests that an auction matches all criteria."""
        auction = Auction(
            id="auction_test",
            gpu_type="NVIDIA A100",
            inventory_quantity=8,
            intranode_interconnect="SXM",
            internode_interconnect="3200_IB",
        )
        criteria = ResourcesSpecification(
            gpu_type="A100",
            num_gpus=8,
            intranode_interconnect="SXM",
            internode_interconnect="3200_IB",
        )
        result = self.auction_finder._matches_criteria(
            auction=auction,
            criteria=criteria,
        )
        self.assertTrue(result)

    def test_matches_criteria_partial_match(self):
        """Tests that an auction partially matches the criteria."""
        auction = Auction(
            id="auction_test",
            gpu_type="NVIDIA A100",
            inventory_quantity=8,
            intranode_interconnect="SXM",
            internode_interconnect="1600_IB",
        )
        criteria = ResourcesSpecification(
            gpu_type="A100",
            num_gpus=8,
            internode_interconnect="3200_IB",
        )
        result = self.auction_finder._matches_criteria(
            auction=auction,
            criteria=criteria,
        )
        self.assertFalse(result)

    def test_matches_criteria_edge_cases(self):
        """Tests matching criteria with edge cases."""
        auction = Auction(id="empty_auction")
        criteria = ResourcesSpecification(
            gpu_type="A100",
            num_gpus=1,
        )
        result = self.auction_finder._matches_criteria(
            auction=auction,
            criteria=criteria,
        )
        self.assertFalse(result)

    def test_find_matching_auctions_with_missing_auction_fields(self):
        """Tests finding matching auctions when some fields are missing."""
        auctions = [Auction(id="auction_missing_fields")]
        criteria = ResourcesSpecification(
            gpu_type="A100",
            num_gpus=1,
        )
        matching_auctions = self.auction_finder.find_matching_auctions(
            auctions=auctions,
            criteria=criteria,
        )
        self.assertEqual(matching_auctions, [])

    def test_find_matching_auctions_substring_matching(self):
        """Tests finding matching auctions with substring-based GPU type."""
        criteria = ResourcesSpecification(
            gpu_type="H100",
            num_gpus=8,
        )
        matching_auctions = self.auction_finder.find_matching_auctions(
            auctions=self.sample_auctions,
            criteria=criteria,
        )
        expected_auctions = [self.sample_auctions[2]]
        self.assertEqual(matching_auctions, expected_auctions)


if __name__ == "__main__":
    unittest.main()

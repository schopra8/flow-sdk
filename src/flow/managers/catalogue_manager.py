import logging
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel

from flow.clients.foundry_client import FoundryClient
from flow.managers.auction_finder import AuctionFinder
from flow.models.instance_type import DetailedInstanceType
from flow.models.pydantic_schemas import Auction


class AugmentedAuction(BaseModel):
    """A richer representation of Auction that includes extra details,
    fetched via FoundryClient or other managers.
    """

    base_auction: Auction
    region_info: Optional[str] = None
    instance_type_info: Optional[str] = None
    resource_spec_info: Optional[str] = None
    detailed_instance_data: Optional[DetailedInstanceType] = None


class CatalogueManager:
    """Manager responsible for fetching and organizing Auctions.

    This manager:
      1. Fetches auctions from Foundry.
      2. Groups and organizes the auctions by GPU type, region, etc.
      3. Writes this organized info:
         - to the console (printing)
         - to a catalogue YAML file.
    """

    def __init__(
        self,
        foundry_client: FoundryClient,
        logger: logging.Logger = None,
        skip_instance_fetch: bool = False,
    ):
        """Initializes the CatalogueManager.

        Args:
            foundry_client: A FoundryClient instance for interacting with the Foundry API.
            logger: A logging.Logger to be used for logging.
            skip_instance_fetch: Whether to skip fetching detailed instance type data.
        """
        self.foundry_client = foundry_client
        self.logger = logger or logging.getLogger(__name__)
        self.skip_instance_fetch = skip_instance_fetch

    def create_catalogue(
        self, project_id: str, output_file: str = "my_auction_catalog.yaml"
    ) -> None:
        """Fetches auctions for a project, organizes them, and writes to a YAML catalogue file.

        Args:
            project_id: Identifier for the project to fetch auctions from.
            output_file: Filepath for writing the resulting catalogue.
        """
        self.logger.info("Fetching auctions for project_id = %s...", project_id)
        auctions = self._fetch_auctions(project_id)

        for auction in auctions:
            self.logger.debug(
                "Fetched Auction: id=%s, instance_type_id=%s, region=%s, gpu_type=%s",
                auction.id,
                auction.instance_type_id,
                auction.region,
                auction.gpu_type,
            )

        self.logger.info("Augmenting auctions for richer details...")
        augmented_auctions = [self._augment_auction_details(a) for a in auctions]

        self.logger.info("Organizing auctions by GPU type + region...")
        grouped_auctions = self._group_auctions_by_gpu_and_region(augmented_auctions)

        self.logger.info("Printing grouped auctions to console...")
        self._print_grouped_auctions(grouped_auctions)

        self.logger.info("Writing grouped auctions to '%s'...", output_file)
        self._write_catalogue_yaml(grouped_auctions, output_file)

        self.logger.info("Catalogue creation complete!")

    def _fetch_auctions(self, project_id: str) -> List[Auction]:
        """Utility method to fetch auctions using AuctionFinder.

        Args:
            project_id: Identifier for the project to fetch auctions from.

        Returns:
            A list of Auction objects.
        """
        auction_finder = AuctionFinder(self.foundry_client)
        return auction_finder.fetch_auctions(project_id)

    def _augment_auction_details(self, auction: Auction) -> AugmentedAuction:
        """Fetches additional metadata about an Auction to build an AugmentedAuction object.

        Args:
            auction: The base Auction object.

        Returns:
            An AugmentedAuction populated with additional metadata.
        """
        self.logger.debug(
            "_augment_auction_details: cluster_id=%s, region=%s, instance_type_id=%s",
            auction.cluster_id,
            auction.region,
            auction.instance_type_id,
        )

        region_info = f"Detailed region info for: {auction.region}"
        instance_type_info = f"Details for instance type: {auction.instance_type_id}"
        resource_spec_info = (
            f"Spec details for resource_spec_id={auction.resource_specification_id}"
        )

        detailed_type: Optional[DetailedInstanceType] = None
        if auction.instance_type_id and not self.skip_instance_fetch:
            try:
                detailed_type = self.foundry_client.get_instance_type(
                    auction.instance_type_id
                )
                self.logger.debug(
                    "Fetched instance type details for %s", auction.instance_type_id
                )
            except Exception as e:
                self.logger.warning(
                    "Could not fetch instance_type details for %s, error=%s",
                    auction.instance_type_id,
                    e,
                )

        return AugmentedAuction(
            base_auction=auction,
            region_info=region_info,
            instance_type_info=instance_type_info,
            resource_spec_info=resource_spec_info,
            detailed_instance_data=detailed_type,
        )

    def _group_auctions_by_gpu_and_region(
        self, augmented_auctions: List[AugmentedAuction]
    ) -> Dict[str, Dict[str, List[AugmentedAuction]]]:
        """Groups AugmentedAuction objects by GPU type and region.

        Args:
            augmented_auctions: List of AugmentedAuction objects.

        Returns:
            Nested dictionary mapping GPU types to region names to lists of AugmentedAuction objects.
        """
        grouped: Dict[str, Dict[str, List[AugmentedAuction]]] = {}
        for aug in augmented_auctions:
            gpu_type = (aug.base_auction.gpu_type or "unknown").lower()
            region_name = aug.base_auction.region or "unknown-region"

            if gpu_type not in grouped:
                grouped[gpu_type] = {}
            if region_name not in grouped[gpu_type]:
                grouped[gpu_type][region_name] = []
            grouped[gpu_type][region_name].append(aug)

        return grouped

    def _print_grouped_auctions(
        self, grouped_auctions: Dict[str, Dict[str, List[AugmentedAuction]]]
    ) -> None:
        """Prints grouped auctions in a human-readable format.

        Args:
            grouped_auctions: Nested dictionary of GPU types and region names mapped to lists of AugmentedAuction objects.
        """
        for gpu_type, regions_data in grouped_auctions.items():
            print(f"\n=== GPU Type: {gpu_type} ===")
            for region, aug_auctions in regions_data.items():
                print(f"  -> Region: {region}")
                for aug in aug_auctions:
                    base = aug.base_auction
                    print(
                        f"     AuctionID: {base.id}, GPUs: {base.inventory_quantity}, "
                        f"Price: {base.last_price}"
                    )
                    print(f"        Region Info: {aug.region_info}")
                    print(f"        Instance Type Info: {aug.instance_type_info}")
                    print(f"        Spec Info: {aug.resource_spec_info}")

                    if aug.detailed_instance_data:
                        instance_type = aug.detailed_instance_data
                        print("        Detailed Instance Type:")
                        print(f"           ID: {instance_type.id}")
                        print(f"           Name: {instance_type.name}")
                        print(f"           num_cpus: {instance_type.num_cpus}")
                        print(f"           num_gpus: {instance_type.num_gpus}")
                        print(f"           memory_gb: {instance_type.memory_gb}")
                        print(f"           architecture: {instance_type.architecture}")

                    all_fields = base.model_dump()
                    print("        Base Auction Fields:")
                    for field_name, field_value in all_fields.items():
                        print(f"           {field_name}: {field_value}")
                    print("")

    def _write_catalogue_yaml(
        self,
        grouped_auctions: Dict[str, Dict[str, List[AugmentedAuction]]],
        filepath: str,
    ) -> None:
        """Writes the grouped auctions into a YAML file.

        Each AugmentedAuction, including nested base_auction details, is serialized via model_dump().

        Args:
            grouped_auctions: Nested dictionary of GPU types and region names mapped to lists of AugmentedAuction objects.
            filepath: The file path to write the YAML data to.
        """
        catalogue_dict = {}
        for gpu_type, regions_data in grouped_auctions.items():
            catalogue_dict[gpu_type] = {}
            for region_name, aug_auctions in regions_data.items():
                catalogue_dict[gpu_type][region_name] = []
                for aug in aug_auctions:
                    catalogue_dict[gpu_type][region_name].append(aug.model_dump())

        with open(filepath, "w", encoding="utf-8") as f:
            yaml.safe_dump(catalogue_dict, f, sort_keys=True)

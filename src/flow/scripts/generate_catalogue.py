#!/usr/bin/env python3
"""Generates an auction catalogue using FoundryClient and CatalogueManager."""

import logging
import os
import sys

from flow.clients.foundry_client import FoundryClient
from flow.managers.catalogue_manager import CatalogueManager


def main():
    """Main entry point for generating an auction catalogue."""
    email = os.environ.get("FOUNDRY_EMAIL")
    password = os.environ.get("FOUNDRY_PASSWORD")

    project_name = os.environ.get("FOUNDRY_PROJECT_NAME")
    if not project_name:
        raise ValueError("No FOUNDRY_PROJECT_NAME environment variable set.")

    skip_instance_fetch = (
        os.environ.get("SKIP_INSTANCE_FETCH", "false").lower() == "true"
    )
    output_file = os.environ.get("CATALOGUE_FILE", "my_auction_catalog.yaml")

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("generate_catalogue")

    logger.info("Instantiating FoundryClient...")
    foundry_client = FoundryClient(email=email, password=password)

    project_id = None
    projects = foundry_client.get_projects()
    for project in projects:
        if project.name == project_name:
            project_id = project.id
            break

    if not project_id:
        raise ValueError(f"Project '{project_name}' not found.")

    if len(sys.argv) > 1:
        project_id = sys.argv[1]

    logger.info("Instantiating CatalogueManager...")
    catalogue_manager = CatalogueManager(
        foundry_client=foundry_client,
        logger=logger,
        skip_instance_fetch=skip_instance_fetch,
    )

    if skip_instance_fetch:
        logger.info(
            "SKIP_INSTANCE_FETCH=True -> No instance type details will be fetched/augmented."
        )

    logger.info(
        "Generating auction catalogue (project_id=%s), output_csv=%s ...",
        project_id,
        output_file,
    )
    catalogue_manager.create_catalogue(project_id=project_id, output_file=output_file)


if __name__ == "__main__":
    main()

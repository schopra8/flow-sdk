import logging
from typing import Any, Dict, List, Optional

import yaml
from pydantic import ValidationError

from .models import (
    TaskManagement,
    ResourcesSpecification,
    Port,
    EphemeralStorageConfig,
    PersistentStorage,
    Networking,
    Resources,
    ConfigModel,
)
from .exceptions import ConfigParserError
from .logging_config import setup_logging

setup_logging()
logger = logging.getLogger("config_parser")

# TODO: add even richer error handling and structure recommendation logic and exception handling.
# TODO: Note, aggregate todos in global github issues or otherwise.


class ConfigParser:
    """Parses and validates the YAML configuration for flow tasks.

    Attributes:
        filename: Path to the YAML configuration file.
        config_data: Raw configuration data from YAML.
        config: Validated configuration model.
    """

    def __init__(self, filename: str) -> None:
        """Initializes the ConfigParser with a YAML configuration file.

        Args:
            filename: The path to the YAML configuration file.

        Raises:
            ConfigParserError: If the file cannot be read or parsed.
        """
        logger.debug("Initializing ConfigParser with file: %s", filename)
        self.filename: str = filename
        self.config_data: Dict[str, Any] = {}
        self.config: Optional[ConfigModel] = None
        self.parse_yaml()
        self.validate_config()

    def parse_yaml(self) -> None:
        """Parses the YAML file and loads the data into config_data.

        Raises:
            ConfigParserError: If the YAML file cannot be read or is malformed.
        """
        logger.debug("Parsing YAML configuration file: %s", self.filename)
        try:
            with open(self.filename, "r", encoding="utf-8") as yaml_file:
                self.config_data = yaml.safe_load(yaml_file) or {}
        except Exception as err:
            error_msg = f"Failed to read configuration file: {err}"
            logger.error(error_msg)
            raise ConfigParserError(error_msg)

    def validate_config(self) -> None:
        """Validates the configuration data using Pydantic models.

        Raises:
            ConfigParserError: If the configuration data is invalid.
        """
        logger.debug("Validating configuration data using Pydantic.")
        try:
            self.config = ConfigModel(**self.config_data)
            logger.debug("Configuration data validated successfully.")
        except ValidationError as validation_err:
            error_messages = []
            for error in validation_err.errors():
                loc = " -> ".join(map(str, error["loc"]))
                msg = f'{loc}: {error["msg"]}'
                error_messages.append(msg)
                logger.error(msg)
            raise ConfigParserError(
                "Configuration validation failed. Please fix the following errors in your YAML file:",
                errors=error_messages,
            )

    def get_task_name(self) -> Optional[str]:
        """Returns the task name from the configuration.

        Returns:
            The name of the task or None if not specified.
        """
        task_name = self.config.name if self.config else None
        logger.info("Retrieved task name: %s", task_name)
        return task_name

    def get_task_management(self) -> Optional[TaskManagement]:
        """Returns the task management configuration.

        Returns:
            The task management configuration or None.
        """
        task_management = self.config.task_management if self.config else None
        logger.debug("Retrieved task management configuration: %s", task_management)
        return task_management

    def get_resources_specification(self) -> ResourcesSpecification:
        """Returns the resources specification from the configuration.

        Raises:
            ConfigParserError: If the resources specification is not available.

        Returns:
            The resources specification.
        """
        if not self.config or not self.config.resources_specification:
            error_msg = "Resources specification is not defined in the configuration."
            logger.error(error_msg)
            raise ConfigParserError(error_msg)
        resources_spec = self.config.resources_specification
        logger.debug("Retrieved resources specification: %s", resources_spec)
        return resources_spec

    def get_ports(self) -> List[Port]:
        """Returns the ports configuration.

        Returns:
            A list of Port instances specified in the configuration.
        """
        port_list = self.config.ports or []
        logger.debug("Retrieved ports: %s", port_list)
        return port_list

    def get_ephemeral_storage_config(self) -> Optional[EphemeralStorageConfig]:
        """Returns the ephemeral storage configuration.

        Returns:
            The ephemeral storage configuration or None.
        """
        ephemeral_storage = (
            self.config.ephemeral_storage_config if self.config else None
        )
        logger.debug("Retrieved ephemeral storage configuration: %s", ephemeral_storage)
        return ephemeral_storage

    def get_persistent_storage(self) -> Optional[PersistentStorage]:
        """Returns the persistent storage configuration.

        Returns:
            The persistent storage configuration or None.
        """
        persistent_storage = self.config.persistent_storage if self.config else None
        logger.debug(
            "Retrieved persistent storage configuration: %s", persistent_storage
        )
        return persistent_storage

    def get_networking(self) -> Optional[Networking]:
        """Returns the networking configuration.

        Returns:
            The networking configuration or None.
        """
        network_config = self.config.networking if self.config else None
        logger.debug("Retrieved networking configuration: %s", network_config)
        return network_config

    def get_resources(self) -> Optional[Resources]:
        """Returns the resources configuration.

        Returns:
            The resources configuration or None.
        """
        resource_config = self.config.resources if self.config else None
        logger.debug("Retrieved resources configuration: %s", resource_config)
        return resource_config

    def get_startup_script(self) -> Optional[str]:
        """Returns the startup script.

        Returns:
            The startup script or None.
        """
        startup_script = self.config.startup_script if self.config else None
        logger.debug("Retrieved startup script.")
        return startup_script

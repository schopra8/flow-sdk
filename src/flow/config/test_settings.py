"""Test environment settings for Foundry.

This module defines the FoundryTestSettings class used to configure
environment variables and other settings specifically for testing.
"""

from .base_settings import FoundryBaseSettings


class FoundryTestSettings(FoundryBaseSettings):
    """Environment settings used for testing.

    This class inherits from FoundryBaseSettings and defines default
    environment variables specifically for the test environment.

    Attributes:
        foundry_email: The Foundry user email address used in the test environment.
        foundry_password: The Foundry user password used in the test environment.
        foundry_project_name: The Foundry project name used in the test environment.
        foundry_ssh_key_name: The Foundry SSH key name used in the test environment.
    """

    foundry_email: str = "test_email@example.com"
    foundry_password: str = "test_password"
    foundry_project_name: str = "test_project"
    foundry_ssh_key_name: str = "test_ssh_key"

    class Config:
        """Pydantic configuration for FoundryTestSettings.

        This configuration points to the '.env.test' file for environment
        variable overrides, if present.
        """

        env_file = ".env.test"

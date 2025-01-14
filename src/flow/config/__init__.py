import os
from typing import Union

from .base_settings import FoundryBaseSettings
from .test_settings import FoundryTestSettings


def get_config() -> Union[FoundryBaseSettings, FoundryTestSettings]:
    """Retrieves Foundry configuration settings.

    Determines which settings to use based on the FLOW_ENV environment variable. If
    FLOW_ENV is set to 'TEST', returns FoundryTestSettings; otherwise returns
    FoundryBaseSettings.

    Returns:
        Union[FoundryBaseSettings, FoundryTestSettings]: The Foundry configuration
            settings based on the environment.
    """
    flow_env: str = os.getenv("FLOW_ENV", "DEV").upper()
    if flow_env == "TEST":
        return FoundryTestSettings()
    return FoundryBaseSettings()

"""flow_config.py

This module retrieves the environment variables required for Foundry
authentication and defines a dictionary for priority price mapping used in
second-price auctions in the FCP. It maintains backward compatibility with
existing usage.
"""

import os
import sys
import warnings

from flow.config import get_config

_settings = get_config()

EMAIL = _settings.foundry_email
PASSWORD = _settings.foundry_password.get_secret_value()
PROJECT_NAME = _settings.foundry_project_name
SSH_KEY_NAME = _settings.foundry_ssh_key_name
PRIORITY_PRICE_MAPPING = _settings.PRIORITY_PRICE_MAPPING


def log_sanitized_settings():
    """
    For debug/log usage: returns a dictionary with
    the password masked, to avoid accidental secret leakage.
    """
    return {
        "foundry_email": _settings.foundry_email,
        "foundry_password": "********",
        "foundry_project_name": _settings.foundry_project_name,
        "foundry_ssh_key_name": _settings.foundry_ssh_key_name,
        "PRIORITY_PRICE_MAPPING": _settings.PRIORITY_PRICE_MAPPING,
    }


# Instructions:
# Please set the following environment variables in your shell before running:
#
# export FOUNDRY_EMAIL='your_email@example.com'
# export FOUNDRY_PASSWORD='your_password'
# export FOUNDRY_PROJECT_NAME='your_project_name'
# export FOUNDRY_SSH_KEY_NAME='your_ssh_key_name'

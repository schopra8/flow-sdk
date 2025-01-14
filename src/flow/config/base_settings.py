import os
from typing import Dict
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, field_validator


class FoundryBaseSettings(BaseSettings):
    """
    Base settings for Foundry environment variables, loading from OS environment
    or from .env if present.
    """

    foundry_email: str = Field(..., alias="FOUNDRY_EMAIL")
    foundry_password: SecretStr = Field(..., alias="FOUNDRY_PASSWORD")
    foundry_project_name: str = Field(..., alias="FOUNDRY_PROJECT_NAME")
    foundry_ssh_key_name: str = Field(..., alias="FOUNDRY_SSH_KEY_NAME")

    PRIORITY_PRICE_MAPPING: Dict[str, float] = Field(
        default={"critical": 14.99, "high": 12.29, "standard": 4.24, "low": 2.00},
        exclude=True,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=True,
        extra="allow",
    )

    @field_validator("foundry_email", "foundry_project_name", "foundry_ssh_key_name")
    @classmethod
    def no_empty_strings(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Required environment variable must not be empty.")
        return value

    @field_validator("foundry_password")
    @classmethod
    def non_empty_password_validator(cls, v: SecretStr):
        if not v or not v.get_secret_value().strip():
            raise ValueError(
                "Required environment variable 'foundry_password' is empty."
            )
        return v

import logging
import uuid
from typing import Any, List, Optional

import requests
from pydantic import ValidationError
from requests import Response
from requests.adapters import HTTPAdapter, Retry

from flow.clients.authenticator import Authenticator
from flow.models import (
    DiskAttachment,
    DiskResponse,
    RegionResponse,
    StorageQuotaResponse,
)
from flow.utils.exceptions import (
    APIError,
    AuthenticationError,
    InvalidResponseError,
    NetworkError,
    TimeoutError,
)

_logger = logging.getLogger(__name__)


class StorageClient:
    """
    A client for interacting with storage resources in the Foundry Cloud Platform.

    This class manages authentication, provides convenience methods for
    creating/retrieving/deleting disks, retrieving storage quotas, listing
    available regions, etc. It uses a requests.Session with built-in retry
    logic and logs at each significant step to simplify debugging.
    """

    DEFAULT_BASE_URL: str = "https://api.mlfoundry.com"

    def __init__(
        self,
        authenticator: Authenticator,
        base_url: Optional[str] = None,
        timeout: int = 10,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize the StorageClient with authentication and session settings.

        Args:
            authenticator: An Authenticator instance used to retrieve an access token.
            base_url: Base URL for the Storage API. Defaults to
                "https://api.mlfoundry.com".
            timeout: The timeout (in seconds) for each network request. Defaults to 10.
            max_retries: The maximum number of retries for failed requests. Defaults to 3.

        Raises:
            TypeError: If `authenticator` is not an instance of Authenticator.
            AuthenticationError: If unable to obtain a valid access token.
        """
        if not isinstance(authenticator, Authenticator):
            raise TypeError("authenticator must be an instance of Authenticator.")

        self._logger = _logger
        self._authenticator = authenticator
        self._base_url = base_url or self.DEFAULT_BASE_URL
        self._timeout = timeout
        self._session = self._create_session(max_retries)

        self._logger.debug("Attempting to retrieve access token.")
        try:
            token = self._authenticator.get_access_token()
            if not token:
                self._logger.error("Failed to obtain token from Authenticator.")
                raise AuthenticationError("Authentication failed: No token received")
        except Exception as exc:
            self._logger.error(
                "Failed to obtain token from Authenticator", exc_info=True
            )
            raise AuthenticationError("Authentication failed") from exc

        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )
        self._logger.debug("StorageClient initialized with base_url=%s", self._base_url)

    def _create_session(self, max_retries: int) -> requests.Session:
        """
        Create and configure a requests.Session with retry logic.

        Args:
            max_retries: The maximum number of retries for HTTP requests.

        Returns:
            A configured requests.Session instance.
        """
        self._logger.debug("Creating session with max_retries=%d", max_retries)
        session = requests.Session()
        retries = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods={"GET", "POST", "DELETE"},
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        self._logger.debug("HTTP session with retries created.")
        return session

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> Response:
        """
        Send an HTTP request and return the response, handling common errors.

        Args:
            method: The HTTP method (e.g. "GET", "POST", "DELETE").
            endpoint: The API endpoint path (e.g. "/marketplace/v1/...").
            **kwargs: Additional keyword arguments for `requests.Session.request()`.

        Returns:
            The requests.Response object from the API call.

        Raises:
            TimeoutError: If the request times out.
            NetworkError: If a network connection error occurs.
            APIError: For other request-related errors (e.g., invalid responses).
        """
        url = f"{self._base_url}{endpoint}"
        kwargs.setdefault("timeout", self._timeout)
        self._logger.debug(
            "Making %s request to %s with kwargs=%s", method, url, kwargs
        )

        try:
            response = self._session.request(method=method, url=url, **kwargs)
            response.raise_for_status()
            self._logger.debug(
                "Request to %s succeeded with status_code=%d.",
                url,
                response.status_code,
            )
            return response

        except requests.exceptions.Timeout as err:
            self._logger.error("Request to %s timed out: %s", url, err)
            raise TimeoutError("Request timed out") from err

        except requests.exceptions.ConnectionError as err:
            self._logger.error(
                "Network error occurred while requesting %s: %s", url, err
            )
            raise NetworkError("Network error occurred") from err

        except requests.exceptions.HTTPError as err:
            if not err.response:
                err.response = response
            self._handle_http_error(err)

        except requests.exceptions.RequestException as err:
            self._logger.error("Request failed for %s: %s", url, err)
            raise APIError(f"Request failed: {err}") from err

        # Generic error fallback
        raise APIError("Unknown error during request execution.")

    def _parse_json(self, response: Response, context: str = "") -> Any:
        """
        Safely parse JSON from a Response object, logging the raw data.

        Args:
            response: The Response from which to parse JSON.
            context: A string indicating the context of this parse, used for logging.

        Returns:
            The parsed JSON data (dict or list).

        Raises:
            ValueError: If the response body is not valid JSON.
        """
        try:
            data = response.json()
            self._logger.debug("Raw JSON for %s: %s", context or "response", data)
            return data
        except ValueError as err:
            self._logger.error(
                "Failed to parse JSON for %s. Error: %s, response text: %s",
                context or "response",
                err,
                response.text,
            )
            raise

    def _handle_http_error(self, error: requests.HTTPError) -> None:
        """
        Handle HTTP errors by logging and raising appropriate exceptions.

        Args:
            error: The HTTPError exception from requests.

        Raises:
            AuthenticationError: If the status code is 401 or 403.
            APIError: For all other non-success HTTP status codes.
        """
        response = error.response
        if response is not None:
            status_code = response.status_code
            content = response.text
            self._logger.error(
                "HTTP error occurred. status_code=%d, response=%s",
                status_code,
                content,
            )
            if status_code in [401, 403]:
                raise AuthenticationError(
                    f"Authentication failed: {content}"
                ) from error
            message = f"API request failed [{status_code}]: {content}"
        else:
            message = "API request failed: No response received"
            self._logger.error(message)

        raise APIError(message) from error

    def _is_valid_uuid(self, value: str) -> bool:
        """
        Check whether a string is a valid UUID.

        Args:
            value: The string to validate.

        Returns:
            True if the string is a valid UUID, False otherwise.
        """
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False

    # -------------------------------------------
    # Public Methods for Storage-Related Actions
    # -------------------------------------------

    def create_disk(
        self, project_id: str, disk_attachment: DiskAttachment
    ) -> DiskResponse:
        """
        Create a new disk in the specified project.

        Args:
            project_id: The ID of the project where the disk is to be created.
            disk_attachment: A DiskAttachment object with details of the disk.

        Returns:
            A DiskResponse object containing the created disk's details.

        Raises:
            ValueError: If the project_id is empty or contains only whitespace.
            InvalidResponseError: If the server response cannot be parsed.
        """
        self._logger.debug(
            "Creating disk with disk_id='%s' in project_id='%s'.",
            disk_attachment.disk_id,
            project_id,
        )
        if not project_id.strip():
            raise ValueError("Project ID must be provided and non-empty.")

        # If region_id is a region name or short region identifier (e.g., "us-central1-a"),
        # we attempt to resolve it to a valid UUID (region_id) by checking existing regions.
        if disk_attachment.region_id and not self._is_valid_uuid(
            disk_attachment.region_id
        ):
            original_region_id = disk_attachment.region_id
            disk_attachment.region_id = self._resolve_region_id(original_region_id)

        payload = {
            "disk_id": disk_attachment.disk_id,
            "name": disk_attachment.name,
            "disk_interface": disk_attachment.disk_interface,
            "region_id": disk_attachment.region_id,
            "size": disk_attachment.size,
            "size_unit": disk_attachment.size_unit,
        }
        self._logger.debug("Payload sent to create_disk: %s", payload)

        endpoint = f"/marketplace/v1/projects/{project_id}/disks"
        response = self._request("POST", endpoint, json=payload)

        try:
            data = self._parse_json(response, context="create_disk response")
            self._logger.debug("Disk created successfully; validating response.")
            disk = DiskResponse.model_validate(data)
            self._logger.debug("Parsed DiskResponse: %s", disk)
            return disk
        except (ValidationError, ValueError) as err:
            self._logger.error("Failed to parse create_disk response: %s", err)
            raise InvalidResponseError(
                "Invalid JSON response from create_disk."
            ) from err

    def get_disks(self, project_id: str) -> List[DiskResponse]:
        """
        Retrieve a list of all disks for the specified project.

        Args:
            project_id: The ID of the project from which to fetch disks.

        Returns:
            A list of DiskResponse objects.

        Raises:
            ValueError: If project_id is empty or whitespace.
            InvalidResponseError: If the response fails validation.
        """
        self._logger.debug("Retrieving disks for project_id='%s'.", project_id)
        if not project_id.strip():
            raise ValueError("project_id must be provided and non-empty.")

        endpoint = f"/marketplace/v1/projects/{project_id}/disks"
        response = self._request("GET", endpoint)

        try:
            data = self._parse_json(response, context="get_disks")
            self._logger.debug("Validating disks data via Pydantic: %s", data)
            disks = [DiskResponse.model_validate(item) for item in data]
            self._logger.debug("Disks successfully validated. Count=%d", len(disks))
            return disks
        except (ValidationError, ValueError) as err:
            self._logger.error("Failed to parse get_disks data: %s", err)
            raise InvalidResponseError("Invalid JSON response from get_disks.") from err

    def get_disk(self, project_id: str, disk_id: str) -> DiskResponse:
        """
        Retrieve details of a specific disk in a given project.

        Args:
            project_id: The project ID.
            disk_id: The disk ID to fetch.

        Returns:
            A DiskResponse object with the disk's details.

        Raises:
            ValueError: If either project_id or disk_id is empty/whitespace.
            InvalidResponseError: If the server response is invalid.
        """
        self._logger.debug(
            "Retrieving disk '%s' for project_id='%s'.", disk_id, project_id
        )
        if not project_id.strip():
            raise ValueError("project_id must be provided and non-empty.")
        if not disk_id.strip():
            raise ValueError("disk_id must be provided and non-empty.")

        endpoint = f"/marketplace/v1/projects/{project_id}/disks/{disk_id}"
        response = self._request("GET", endpoint)

        try:
            data = self._parse_json(response, context="get_disk")
            self._logger.debug("Validating disk data via Pydantic: %s", data)
            disk = DiskResponse.model_validate(data)
            self._logger.debug("Disk successfully validated: %s", disk)
            return disk
        except (ValidationError, ValueError) as err:
            self._logger.error("Failed to parse get_disk data: %s", err)
            raise InvalidResponseError("Invalid JSON response from get_disk.") from err

    def delete_disk(self, project_id: str, disk_id: str) -> None:
        """
        Delete a disk from a specified project.

        Args:
            project_id: The ID of the project.
            disk_id: The ID of the disk to delete.

        Raises:
            ValueError: If project_id or disk_id is empty or whitespace.
            APIError: If the deletion request fails.
        """
        self._logger.debug(
            "Deleting disk_id='%s' from project_id='%s'.", disk_id, project_id
        )
        if not project_id.strip():
            raise ValueError("project_id must be provided and non-empty.")
        if not disk_id.strip():
            raise ValueError("disk_id must be provided and non-empty.")

        endpoint = f"/marketplace/v1/projects/{project_id}/disks/{disk_id}"
        self._request("DELETE", endpoint)
        self._logger.info(
            "Disk '%s' successfully deleted from project '%s'.", disk_id, project_id
        )

    def get_storage_quota(self, project_id: str) -> StorageQuotaResponse:
        """
        Retrieve the storage quota for a given project.

        Args:
            project_id: The ID of the project to query.

        Returns:
            A StorageQuotaResponse object containing the quota information.

        Raises:
            ValueError: If project_id is empty or whitespace.
            InvalidResponseError: If the server response is invalid.
        """
        self._logger.debug("Retrieving storage quota for project_id='%s'.", project_id)
        if not project_id.strip():
            raise ValueError("project_id must be provided and non-empty.")

        endpoint = f"/marketplace/v1/projects/{project_id}/disks/quotas"
        response = self._request("GET", endpoint)

        try:
            data = self._parse_json(response, context="get_storage_quota")
            self._logger.debug("Validating storage quota via Pydantic: %s", data)
            quota = StorageQuotaResponse.model_validate(data)
            self._logger.debug("StorageQuotaResponse successfully validated: %s", quota)
            return quota
        except (ValidationError, ValueError) as err:
            self._logger.error("Failed to parse storage quota data: %s", err)
            raise InvalidResponseError(
                "Invalid JSON response from get_storage_quota."
            ) from err

    def get_regions(self) -> List[RegionResponse]:
        """
        Retrieve all available regions in the marketplace.

        Returns:
            A list of RegionResponse objects.

        Raises:
            InvalidResponseError: If the server response is invalid or not JSON.
        """
        self._logger.debug("Retrieving list of regions.")
        endpoint = "/marketplace/v1/regions"
        response = self._request("GET", endpoint)

        try:
            data = self._parse_json(response, context="get_regions")
            # The API might return a single dict or a list of dicts
            if isinstance(data, dict):
                data = [data]
            elif not isinstance(data, list):
                raise ValueError(
                    f"Expected either dict or list for regions, got: {type(data)}. Data: {data}"
                )

            self._logger.debug("Validating region data with Pydantic: %s", data)
            regions = [RegionResponse.model_validate(item) for item in data]
            self._logger.debug("Regions successfully validated. Count=%d", len(regions))
            return regions
        except (ValueError, ValidationError) as err:
            self._logger.error("Failed to parse get_regions data: %s", err)
            raise InvalidResponseError(f"Invalid response format: {err}") from err

    def _resolve_region_id(self, region_str: str) -> str:
        """
        Attempt to resolve a region string (e.g. "us-central1-a") to a valid region UUID.

        This is done by comparing against the list of known regions returned by
        `get_regions()`. First we look if the input matches a region_id exactly;
        if not, we look for a matching region's name. If no match is found, raises ValueError.

        Args:
            region_str: A region string that could be either an actual region_id or a region name.

        Returns:
            The resolved region_id as a UUID string.

        Raises:
            ValueError: If no match is found in the known regions.
        """
        self._logger.debug(
            "Resolving region string '%s' into a valid region_id.", region_str
        )
        all_regions = self.get_regions()
        for region_info in all_regions:
            if region_info.region_id == region_str:
                self._logger.debug(
                    "Matched region_str='%s' to region_id='%s' directly.",
                    region_str,
                    region_info.region_id,
                )
                return region_info.region_id

        for region_info in all_regions:
            if region_info.name == region_str:
                self._logger.debug(
                    "Matched region_str='%s' to region name='%s', region_id='%s'.",
                    region_str,
                    region_info.name,
                    region_info.region_id,
                )
                return region_info.region_id

        raise ValueError(f"No matching region found for '{region_str}'")

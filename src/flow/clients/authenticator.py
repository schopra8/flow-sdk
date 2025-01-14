import logging
import os
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter, Retry

from flow.utils.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    NetworkError,
    TimeoutError,
)

logger = logging.getLogger(__name__)


class Authenticator:
    """Handles user authentication and access token retrieval.

    This class encapsulates logic for sending authentication requests to the FCP auth
    API and storing the resulting access token. Upon initialization, the class
    immediately attempts to authenticate using provided credentials.

    Attributes:
        email: The user's email address.
        password: The user's password.
        api_url: The base URL for the authentication API.
        request_timeout: Timeout value, in seconds, for the HTTP request.
        session: A configured `requests.Session` with a retry strategy.
        access_token: The string token returned upon successful authentication.
    """

    def __init__(
        self,
        email: str,
        password: str,
        api_url: Optional[str] = None,
        request_timeout: int = 10,
        max_retries: int = 3,
    ) -> None:
        """Initializes the Authenticator with user credentials.

        Args:
            email: The user's email address.
            password: The user's password.
            api_url: (Optional) The base URL for the authentication API. If not
                provided, uses 'https://api.mlfoundry.com' or an environment
                variable named 'API_URL' if set.
            request_timeout: (Optional) The request timeout in seconds.
                Defaults to 10.
            max_retries: (Optional) Maximum number of retry attempts for
                HTTP requests. Defaults to 3.

        Raises:
            TypeError: If the email or password is not a string.
            ValueError: If the email or password is empty.
        """
        if not isinstance(email, str):
            raise TypeError("Email must be a string.")
        if not isinstance(password, str):
            raise TypeError("Password must be a string.")
        if not email:
            raise ValueError("Email must not be empty.")
        if not password:
            raise ValueError("Password must not be empty.")

        self.email: str = email
        self.password: str = password
        self.api_url: str = api_url or os.getenv("API_URL", "https://api.mlfoundry.com")
        self.request_timeout: int = request_timeout
        self.session: requests.Session = self._create_session(max_retries)
        self.access_token: str = self.authenticate()

    def _create_session(self, max_retries: int) -> requests.Session:
        """Creates and configures an HTTP session with a retry strategy.

        Args:
            max_retries: Maximum number of retry attempts for HTTP requests.

        Returns:
            A configured `requests.Session` object with retry behavior.
        """
        session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods={"POST"},
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        logger.debug(
            "Created a new HTTP session with retries configured.",
            extra={
                "max_retries": max_retries,
                "backoff_factor": 0.5,
            },
        )
        return session

    def authenticate(self) -> str:
        """Authenticates the user and retrieves an access token.

        Sends a POST request to the configured API URL with the user credentials.

        Returns:
            The retrieved access token as a string.

        Raises:
            InvalidCredentialsError: If the provided credentials are invalid.
            NetworkError: If a network-related error occurs.
            TimeoutError: If the authentication request times out.
            AuthenticationError: If any other authentication-related error occurs.
        """
        auth_payload: Dict[str, str] = {
            "email": self.email,
            "password": self.password,
        }
        login_url = f"{self.api_url}/login"

        logger.debug(
            "Attempting to authenticate user.",
            extra={
                "url": login_url,
                "email_provided": bool(self.email),
            },
        )

        try:
            response = self.session.post(
                login_url,
                json=auth_payload,
                timeout=self.request_timeout,
                headers={"Content-Type": "application/json"},
            )
        except requests.exceptions.Timeout as timeout_error:
            logger.exception("Authentication request timed out.")
            raise TimeoutError("Authentication request timed out.") from timeout_error
        except requests.exceptions.ConnectionError as conn_error:
            logger.exception("Network error during authentication.")
            raise NetworkError(
                "Network error occurred during authentication."
            ) from conn_error
        except requests.exceptions.RequestException as req_error:
            logger.exception("General request exception during authentication.")
            raise AuthenticationError("Authentication request failed.") from req_error

        # Handle HTTP error responses
        if response.status_code >= 400:
            logger.error(
                "Authentication failed.",
                extra={
                    "status_code": response.status_code,
                    "url": login_url,
                    "email": self.email,
                },
            )
            if response.status_code == 401:
                raise InvalidCredentialsError("Invalid email or password.")
            raise AuthenticationError(
                f"Authentication failed with status code {response.status_code}."
            )

        # Parse JSON response
        try:
            response_data: Dict[str, Any] = response.json()
        except ValueError as json_error:
            logger.exception("Unable to decode the response as JSON.")
            raise AuthenticationError("Invalid response format.") from json_error

        access_token: Optional[str] = response_data.get("access_token")
        if not access_token:
            logger.error(
                "Access token not found in response.",
                extra={
                    "response_data": response_data,
                    "url": login_url,
                },
            )
            raise AuthenticationError("Access token not found in response.")

        logger.info("Authentication succeeded and access token retrieved.")
        return access_token

    def get_access_token(self) -> str:
        """Retrieves the authenticated access token.

        Returns:
            The access token string.
        """
        return self.access_token

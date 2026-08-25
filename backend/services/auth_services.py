"""
Azure authentication service
Handles token generation and caching with automatic refresh
"""
import ssl
import os
import urllib3
import requests
from datetime import datetime, timedelta
from threading import Lock
from typing import Optional

from core.config import AzureConfig
from core.exceptions import AuthenticationError
from core.logging_config import get_logger

logger = get_logger(__name__)

if os.getenv("ENABLE_SSL_VERIFY", "true").lower() == "false":
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logger.warning("SSL verification disabled - NOT recommended for production")


class AzureAuthService:
    """Manages Azure AD authentication with token caching and refresh"""
    
    def __init__(self, config: AzureConfig, verify_ssl: bool = False):
        self.config = config
        self.verify_ssl = verify_ssl
        self._token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._lock = Lock()
        
        logger.info("AzureAuthService initialized")
    
    def get_bearer_token(self, force_refresh: bool = False) -> str:
        """
        Get Azure AD bearer token with caching
        
        Args:
            force_refresh: Force token refresh even if cached token is valid
            
        Returns:
            Bearer token string
            
        Raises:
            AuthenticationError: If token acquisition fails
        """
        with self._lock:
            # Check if cached token is still valid
            if not force_refresh and self._token and self._token_expires_at:
                # Refresh 5 minutes before expiry
                if datetime.now() < (self._token_expires_at - timedelta(minutes=5)):
                    logger.debug("Using cached Azure AD token")
                    return self._token
            
            # Request new token
            logger.info("Requesting new Azure AD token")
            try:
                token_url = (
                    f"https://login.microsoftonline.com/{self.config.tenant_id}"
                    "/oauth2/v2.0/token"
                )
                
                response = requests.post(
                    token_url,
                    data={
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret,
                        "grant_type": "client_credentials",
                        "scope": "api://a18b5274-e7df-4ae7-a9af-b5d200dd200f/.default"
                    },
                    verify=self.verify_ssl,
                    timeout=30
                )
                response.raise_for_status()
                
                token_data = response.json()
                access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)
                
                if not access_token:
                    raise AuthenticationError("No access_token in response")
                
                # Cache token
                self._token = f"Bearer {access_token}"
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info(f"Azure AD token acquired, expires in {expires_in}s")
                return self._token
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Failed to acquire Azure AD token: {str(e)}"
                logger.error(error_msg)
                raise AuthenticationError(
                    error_msg,
                    details={"tenant_id": self.config.tenant_id}
                )
    
    def invalidate_token(self):
        """Invalidate cached token (useful for testing or error recovery)"""
        with self._lock:
            self._token = None
            self._token_expires_at = None
            logger.info("Azure AD token invalidated")

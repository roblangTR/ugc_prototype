"""
Thomson Reuters Authentication Module

This module handles authentication with Thomson Reuters AI Platform
and manages tokens for Google Gemini access via Vertex AI.

Based on TR Authentication & Gemini Integration specification.
"""

import os
import logging
from typing import Optional, Tuple, Dict
from datetime import datetime
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass


class TokenExpiredError(Exception):
    """Raised when token has expired"""
    pass


class WorkspaceError(Exception):
    """Raised when workspace configuration is invalid"""
    pass


class ThomsonReutersAuth:
    """
    Handle authentication with Thomson Reuters AI Platform and manage tokens
    for Gemini access.
    
    This class provides:
    - Token retrieval from TR authentication service
    - Token refresh mechanism
    - Credential management for Vertex AI initialization
    """
    
    def __init__(self):
        """Initialize authentication handler"""
        self.workspace_id = os.getenv('WORKSPACE_ID')
        self.model_name = os.getenv('MODEL_NAME', 'gemini-2.0-flash-exp')
        self.credentials_url = os.getenv('CREDENTIALS_URL')
        self._token: Optional[str] = None
        self.project_id: Optional[str] = None
        self.region: Optional[str] = None
        self._token_timestamp: Optional[datetime] = None
        
        self._validate_config()
    
    def _validate_config(self):
        """Validate required configuration"""
        if not self.workspace_id:
            raise ValueError("WORKSPACE_ID not found in environment variables")
        if not self.credentials_url:
            raise ValueError("CREDENTIALS_URL not found in environment variables")
        
        # Ensure types are correct for type checking
        assert isinstance(self.workspace_id, str)
        assert isinstance(self.credentials_url, str)
        
        logger.info(f"Authentication configured for workspace: {self.workspace_id}")
        logger.info(f"Model: {self.model_name}")
    
    def get_token(self) -> str:
        """
        Get authentication token from TR platform
        
        Returns:
            str: Authentication token
            
        Raises:
            AuthenticationError: If token retrieval fails
            WorkspaceError: If workspace configuration is invalid
        """
        try:
            logger.info("[AUTH] Token request initiated")
            
            # Ensure credentials_url is not None (already validated in __init__)
            if not self.credentials_url:
                raise AuthenticationError("Credentials URL not configured")
            
            payload = {
                'workspace_id': self.workspace_id,
                'model_name': self.model_name
            }
            
            response = requests.post(
                self.credentials_url,
                json=payload,
                timeout=int(os.getenv('TOKEN_TIMEOUT_SECONDS', '10'))
            )
            
            # Handle specific error codes
            if response.status_code == 401:
                raise AuthenticationError("Invalid workspace credentials")
            elif response.status_code == 403:
                raise WorkspaceError("Workspace does not have access to this model")
            elif response.status_code == 429:
                raise AuthenticationError("Rate limit exceeded")
            
            response.raise_for_status()
            
            data = response.json()
            self._token = data.get('token')
            
            if not self._token:
                raise AuthenticationError("Token not found in response")
            
            self.project_id = data.get('project_id')
            self.region = data.get('region')
            self._token_timestamp = datetime.now()
            
            logger.info(f"[AUTH] ✓ Token obtained successfully for workspace: {self.workspace_id}")
            logger.info(f"[AUTH] Project: {self.project_id}, Region: {self.region}")
            
            return self._token
            
        except requests.exceptions.Timeout:
            logger.error("[AUTH] ✗ Authentication service timeout")
            raise AuthenticationError("Authentication service timeout")
        except requests.exceptions.ConnectionError:
            logger.error("[AUTH] ✗ Cannot connect to authentication service")
            raise AuthenticationError("Cannot connect to authentication service")
        except requests.exceptions.RequestException as e:
            logger.error(f"[AUTH] ✗ Token request failed: {e}")
            raise AuthenticationError(f"Failed to retrieve authentication token: {e}")
    
    def refresh_token(self) -> str:
        """
        Refresh the authentication token
        
        Returns:
            str: New authentication token
        """
        logger.info("[AUTH] Token refresh initiated")
        return self.get_token()
    
    def get_credentials(self) -> Dict[str, str]:
        """
        Get full credentials including token, project_id, and region
        
        Returns:
            dict: Credentials dictionary with token, project_id, and region
            
        Raises:
            RuntimeError: If credentials are not available
        """
        if not self._token:
            self.get_token()
        
        # Ensure all required fields are present
        if not self._token or not self.project_id or not self.region:
            raise RuntimeError("Incomplete credentials - token, project_id, or region missing")
        
        return {
            'token': self._token,
            'project_id': self.project_id,
            'region': self.region
        }
    
    def is_token_valid(self) -> bool:
        """
        Check if current token is still valid (basic check)
        
        Returns:
            bool: True if token exists, False otherwise
        """
        return self._token is not None
    
    def get_token_age_minutes(self) -> Optional[float]:
        """
        Get the age of the current token in minutes
        
        Returns:
            float: Token age in minutes, or None if no token
        """
        if not self._token_timestamp:
            return None
        
        age = datetime.now() - self._token_timestamp
        return age.total_seconds() / 60


# Global singleton instance
_auth_instance: Optional[ThomsonReutersAuth] = None


def initialize_auth() -> Tuple[str, str]:
    """
    Initialize Thomson Reuters authentication
    
    This should be called once at application startup.
    
    Returns:
        tuple: (workspace_id, model_name)
        
    Raises:
        ValueError: If configuration is invalid
        AuthenticationError: If authentication fails
    """
    global _auth_instance
    
    try:
        _auth_instance = ThomsonReutersAuth()
        _auth_instance.get_token()
        
        # Ensure workspace_id is not None
        if not _auth_instance.workspace_id:
            raise RuntimeError("Workspace ID not available after initialization")
        
        logger.info("=" * 60)
        logger.info("✓ Thomson Reuters AI Platform initialized")
        logger.info(f"  Workspace: {_auth_instance.workspace_id}")
        logger.info(f"  Model: {_auth_instance.model_name}")
        logger.info(f"  Project: {_auth_instance.project_id}")
        logger.info(f"  Region: {_auth_instance.region}")
        logger.info("=" * 60)
        
        return _auth_instance.workspace_id, _auth_instance.model_name
        
    except Exception as e:
        logger.error(f"✗ Authentication initialization failed: {e}")
        raise


def get_auth_instance() -> ThomsonReutersAuth:
    """
    Get the global authentication instance
    
    Returns:
        ThomsonReutersAuth: The global authentication instance
        
    Raises:
        RuntimeError: If authentication not initialized
    """
    if _auth_instance is None:
        raise RuntimeError(
            "Authentication not initialized. Call initialize_auth() first."
        )
    return _auth_instance


def safe_log_auth():
    """Log authentication info without exposing tokens"""
    try:
        auth = get_auth_instance()
        logger.info("Authentication Status:")
        logger.info(f"  Workspace: {auth.workspace_id}")
        logger.info(f"  Model: {auth.model_name}")
        logger.info(f"  Token: {'*' * 20} (masked)")
        logger.info(f"  Project: {auth.project_id}")
        logger.info(f"  Region: {auth.region}")
        
        token_age = auth.get_token_age_minutes()
        if token_age:
            logger.info(f"  Token Age: {token_age:.1f} minutes")
    except RuntimeError as e:
        logger.warning(f"Cannot log auth status: {e}")


if __name__ == "__main__":
    # Test authentication when run directly
    try:
        print("Testing Thomson Reuters Authentication...")
        workspace_id, model_name = initialize_auth()
        print(f"\n✓ Authentication successful!")
        print(f"  Workspace: {workspace_id}")
        print(f"  Model: {model_name}")
        
        # Test credential retrieval
        auth = get_auth_instance()
        creds = auth.get_credentials()
        print(f"\n✓ Credentials retrieved:")
        print(f"  Project ID: {creds['project_id']}")
        print(f"  Region: {creds['region']}")
        print(f"  Token: {'*' * 20} (masked)")
        
    except Exception as e:
        print(f"\n✗ Authentication failed: {e}")
        exit(1)

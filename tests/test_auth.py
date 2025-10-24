"""
Unit tests for Thomson Reuters Authentication Module
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
import os
from datetime import datetime

# Import the module to test
from modules.auth import (
    ThomsonReutersAuth,
    initialize_auth,
    get_auth_instance,
    AuthenticationError,
    WorkspaceError,
    TokenExpiredError
)


class TestThomsonReutersAuth:
    """Test cases for ThomsonReutersAuth class"""
    
    @patch.dict(os.environ, {
        'WORKSPACE_ID': 'test-workspace',
        'MODEL_NAME': 'gemini-2.0-flash-exp',
        'CREDENTIALS_URL': 'https://test-auth.example.com/api/token'
    })
    def test_init_success(self):
        """Test successful initialization with valid environment variables"""
        auth = ThomsonReutersAuth()
        
        assert auth.workspace_id == 'test-workspace'
        assert auth.model_name == 'gemini-2.0-flash-exp'
        assert auth.credentials_url == 'https://test-auth.example.com/api/token'
        assert auth._token is None
        assert auth.project_id is None
        assert auth.region is None
    
    @patch.dict(os.environ, {}, clear=True)
    def test_init_missing_workspace_id(self):
        """Test initialization fails when WORKSPACE_ID is missing"""
        with pytest.raises(ValueError, match="WORKSPACE_ID not found"):
            ThomsonReutersAuth()
    
    @patch.dict(os.environ, {'WORKSPACE_ID': 'test-workspace'}, clear=True)
    def test_init_missing_credentials_url(self):
        """Test initialization fails when CREDENTIALS_URL is missing"""
        with pytest.raises(ValueError, match="CREDENTIALS_URL not found"):
            ThomsonReutersAuth()
    
    @patch.dict(os.environ, {
        'WORKSPACE_ID': 'test-workspace',
        'CREDENTIALS_URL': 'https://test-auth.example.com/api/token'
    })
    @patch('modules.auth.requests.post')
    def test_get_token_success(self, mock_post):
        """Test successful token retrieval"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'token': 'test-token-123',
            'project_id': 'test-project',
            'region': 'us-central1'
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        auth = ThomsonReutersAuth()
        token = auth.get_token()
        
        assert token == 'test-token-123'
        assert auth._token == 'test-token-123'
        assert auth.project_id == 'test-project'
        assert auth.region == 'us-central1'
        assert auth._token_timestamp is not None
        
        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://test-auth.example.com/api/token'
        assert call_args[1]['json']['workspace_id'] == 'test-workspace'
    
    @patch.dict(os.environ, {
        'WORKSPACE_ID': 'test-workspace',
        'CREDENTIALS_URL': 'https://test-auth.example.com/api/token'
    })
    @patch('modules.auth.requests.post')
    def test_get_token_401_error(self, mock_post):
        """Test handling of 401 Unauthorized error"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        auth = ThomsonReutersAuth()
        
        with pytest.raises(AuthenticationError, match="Invalid workspace credentials"):
            auth.get_token()
    
    @patch.dict(os.environ, {
        'WORKSPACE_ID': 'test-workspace',
        'CREDENTIALS_URL': 'https://test-auth.example.com/api/token'
    })
    @patch('modules.auth.requests.post')
    def test_get_token_403_error(self, mock_post):
        """Test handling of 403 Forbidden error"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_post.return_value = mock_response
        
        auth = ThomsonReutersAuth()
        
        with pytest.raises(WorkspaceError, match="does not have access"):
            auth.get_token()
    
    @patch.dict(os.environ, {
        'WORKSPACE_ID': 'test-workspace',
        'CREDENTIALS_URL': 'https://test-auth.example.com/api/token'
    })
    @patch('modules.auth.requests.post')
    def test_get_token_429_error(self, mock_post):
        """Test handling of 429 Rate Limit error"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response
        
        auth = ThomsonReutersAuth()
        
        with pytest.raises(AuthenticationError, match="Rate limit exceeded"):
            auth.get_token()
    
    @patch.dict(os.environ, {
        'WORKSPACE_ID': 'test-workspace',
        'CREDENTIALS_URL': 'https://test-auth.example.com/api/token'
    })
    @patch('modules.auth.requests.post')
    def test_get_token_timeout(self, mock_post):
        """Test handling of timeout error"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        auth = ThomsonReutersAuth()
        
        with pytest.raises(AuthenticationError, match="timeout"):
            auth.get_token()
    
    @patch.dict(os.environ, {
        'WORKSPACE_ID': 'test-workspace',
        'CREDENTIALS_URL': 'https://test-auth.example.com/api/token'
    })
    @patch('modules.auth.requests.post')
    def test_get_token_connection_error(self, mock_post):
        """Test handling of connection error"""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        auth = ThomsonReutersAuth()
        
        with pytest.raises(AuthenticationError, match="Cannot connect"):
            auth.get_token()
    
    @patch.dict(os.environ, {
        'WORKSPACE_ID': 'test-workspace',
        'CREDENTIALS_URL': 'https://test-auth.example.com/api/token'
    })
    @patch('modules.auth.requests.post')
    def test_get_token_missing_token_in_response(self, mock_post):
        """Test handling when token is missing from response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'project_id': 'test-project',
            'region': 'us-central1'
            # token is missing
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        auth = ThomsonReutersAuth()
        
        with pytest.raises(AuthenticationError, match="Token not found in response"):
            auth.get_token()
    
    @patch.dict(os.environ, {
        'WORKSPACE_ID': 'test-workspace',
        'CREDENTIALS_URL': 'https://test-auth.example.com/api/token'
    })
    @patch('modules.auth.requests.post')
    def test_refresh_token(self, mock_post):
        """Test token refresh mechanism"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'token': 'new-token-456',
            'project_id': 'test-project',
            'region': 'us-central1'
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        auth = ThomsonReutersAuth()
        auth._token = 'old-token-123'
        
        new_token = auth.refresh_token()
        
        assert new_token == 'new-token-456'
        assert auth._token == 'new-token-456'
    
    @patch.dict(os.environ, {
        'WORKSPACE_ID': 'test-workspace',
        'CREDENTIALS_URL': 'https://test-auth.example.com/api/token'
    })
    @patch('modules.auth.requests.post')
    def test_get_credentials(self, mock_post):
        """Test getting full credentials"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'token': 'test-token-123',
            'project_id': 'test-project',
            'region': 'us-central1'
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        auth = ThomsonReutersAuth()
        creds = auth.get_credentials()
        
        assert creds['token'] == 'test-token-123'
        assert creds['project_id'] == 'test-project'
        assert creds['region'] == 'us-central1'
    
    @patch.dict(os.environ, {
        'WORKSPACE_ID': 'test-workspace',
        'CREDENTIALS_URL': 'https://test-auth.example.com/api/token'
    })
    def test_is_token_valid(self):
        """Test token validity check"""
        auth = ThomsonReutersAuth()
        
        # No token initially
        assert auth.is_token_valid() is False
        
        # Set a token
        auth._token = 'test-token'
        assert auth.is_token_valid() is True
    
    @patch.dict(os.environ, {
        'WORKSPACE_ID': 'test-workspace',
        'CREDENTIALS_URL': 'https://test-auth.example.com/api/token'
    })
    def test_get_token_age_minutes(self):
        """Test getting token age in minutes"""
        auth = ThomsonReutersAuth()
        
        # No token timestamp initially
        assert auth.get_token_age_minutes() is None
        
        # Set a token timestamp
        auth._token_timestamp = datetime.now()
        age = auth.get_token_age_minutes()
        
        assert age is not None
        assert age >= 0
        assert age < 1  # Should be less than 1 minute old


class TestGlobalAuthFunctions:
    """Test cases for global authentication functions"""
    
    @patch.dict(os.environ, {
        'WORKSPACE_ID': 'test-workspace',
        'MODEL_NAME': 'gemini-2.0-flash-exp',
        'CREDENTIALS_URL': 'https://test-auth.example.com/api/token'
    })
    @patch('modules.auth.requests.post')
    def test_initialize_auth_success(self, mock_post):
        """Test successful authentication initialization"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'token': 'test-token-123',
            'project_id': 'test-project',
            'region': 'us-central1'
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Reset global instance
        import modules.auth
        modules.auth._auth_instance = None
        
        workspace_id, model_name = initialize_auth()
        
        assert workspace_id == 'test-workspace'
        assert model_name == 'gemini-2.0-flash-exp'
        
        # Verify global instance was created
        auth = get_auth_instance()
        assert auth is not None
        assert auth.workspace_id == 'test-workspace'
    
    def test_get_auth_instance_not_initialized(self):
        """Test getting auth instance when not initialized"""
        # Reset global instance
        import modules.auth
        modules.auth._auth_instance = None
        
        with pytest.raises(RuntimeError, match="Authentication not initialized"):
            get_auth_instance()
    
    @patch.dict(os.environ, {
        'WORKSPACE_ID': 'test-workspace',
        'MODEL_NAME': 'gemini-2.0-flash-exp',
        'CREDENTIALS_URL': 'https://test-auth.example.com/api/token'
    })
    @patch('modules.auth.requests.post')
    def test_initialize_auth_failure(self, mock_post):
        """Test authentication initialization failure"""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        # Reset global instance
        import modules.auth
        modules.auth._auth_instance = None
        
        with pytest.raises(AuthenticationError):
            initialize_auth()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

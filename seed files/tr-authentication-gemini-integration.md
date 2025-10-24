# Thomson Reuters Authentication & Gemini Integration

## Authentication System Overview

The UGC Video Metadata Generation App uses Thomson Reuters' centralized authentication system to securely access Google Gemini via Vertex AI.

### Architecture

```
User Request
    ↓
TR Auth Service (CREDENTIALS_URL)
    ├─ Input: workspace_id, model_name
    └─ Output: token, project_id, region
    ↓
Vertex AI Initialization
    ├─ OAuth2Credentials(token)
    ├─ project_id
    └─ region (location)
    ↓
Gemini Model Access
```

---

## Environment Configuration

### Required Environment Variables

```bash
# .env file
WORKSPACE_ID=your-workspace-id
MODEL_NAME=gemini-2.0-flash-exp
CREDENTIALS_URL=https://your-tr-credentials-endpoint.com/api/token
```

### Configuration Details

| Variable | Description | Example |
|----------|-------------|---------|
| `WORKSPACE_ID` | Thomson Reuters workspace identifier | `tr-newsroom-prod` |
| `MODEL_NAME` | Gemini model to use | `gemini-2.0-flash-exp` |
| `CREDENTIALS_URL` | TR authentication endpoint | `https://auth.tr.com/api/token` |

---

## Authentication Module (`auth.py`)

### Class: `ThomsonReutersAuth`

**Purpose:** Handle authentication with Thomson Reuters AI Platform and manage tokens for Gemini access.

**Key Methods:**

```python
class ThomsonReutersAuth:
    def __init__(self):
        """Initialize authentication handler"""
        self.workspace_id = os.getenv('WORKSPACE_ID')
        self.model_name = os.getenv('MODEL_NAME', 'gemini-2.0-flash-exp')
        self.credentials_url = os.getenv('CREDENTIALS_URL')
        self._token = None
        self._validate_config()
    
    def get_token(self) -> str:
        """Get authentication token from TR platform"""
        payload = {
            'workspace_id': self.workspace_id,
            'model_name': self.model_name
        }
        
        response = requests.post(
            self.credentials_url,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        self._token = data.get('token')
        self.project_id = data.get('project_id')
        self.region = data.get('region')
        
        return self._token
    
    def get_credentials(self) -> dict:
        """Get full credentials including token, project_id, and region"""
        if not self._token:
            self.get_token()
        
        return {
            'token': self._token,
            'project_id': self.project_id,
            'region': self.region
        }
```

### Global Authentication Instance

```python
# Global singleton pattern
_auth_instance: Optional[ThomsonReutersAuth] = None

def initialize_auth() -> Tuple[str, str]:
    """Initialize Thomson Reuters authentication"""
    global _auth_instance
    
    _auth_instance = ThomsonReutersAuth()
    _auth_instance.get_token()
    
    print(f"✓ Thomson Reuters AI Platform initialized")
    print(f"  Workspace: {_auth_instance.workspace_id}")
    print(f"  Model: {_auth_instance.model_name}")
    
    return _auth_instance.workspace_id, _auth_instance.model_name

def get_auth_instance() -> ThomsonReutersAuth:
    """Get the global authentication instance"""
    if _auth_instance is None:
        raise RuntimeError("Authentication not initialized. Call initialize_auth() first.")
    return _auth_instance
```

---

## Gemini Enhancer Module

### Class: `GeminiEnhancer`

**Purpose:** Handles video enhancement using Gemini API via Vertex AI SDK with TR authentication.

### Initialization

```python
from google.oauth2.credentials import Credentials as OAuth2Credentials
import vertexai
from vertexai.generative_models import GenerativeModel, Part

class GeminiEnhancer:
    def __init__(self):
        """Initialize the Gemini enhancer with TR auth"""
        self.auth = get_auth_instance()
        self.model = None
        self._initialize_vertex()
        logging.info(f"Gemini enhancer initialized with model: {self.auth.model_name}")
    
    def _initialize_vertex(self):
        """Initialize Vertex AI with Thomson Reuters credentials"""
        try:
            # Get credentials from auth module
            creds_data = self.auth.get_credentials()
            
            # Create OAuth2 credentials
            temp_creds = OAuth2Credentials(creds_data['token'])
            
            # Initialize Vertex AI
            vertexai.init(
                project=creds_data['project_id'],
                location=creds_data['region'],
                credentials=temp_creds
            )
            
            # Load system instruction
            system_instruction = self._load_system_instruction()
            
            # Create the model
            self.model = GenerativeModel(
                model_name=self.auth.model_name,
                system_instruction=system_instruction
            )
            
            logging.info("Vertex AI initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing Vertex AI: {e}")
            raise
```

### System Instruction

```python
def _load_system_instruction(self) -> str:
    """Load system instruction for the model"""
    instruction = """You are an expert video analyst specializing in news and documentary footage analysis.

Your task is to analyze video clips and provide detailed, structured metadata in JSON format.

For each video clip, you should:
1. Provide an enhanced natural language description of what you see
2. Classify the shot type, size, and camera movement
3. Describe the composition and lighting
4. Identify primary subjects and actions
5. Assess visual quality
6. Determine the tone and news context

Be precise, objective, and thorough in your analysis. Focus on visual elements that would be important for video editing and news production."""
    
    return instruction
```

### Video Analysis with Shotlist Matching

```python
def enhance_clip(
    self,
    video_path: str,
    shotlist: Dict[str, Any],
    clip_id: str,
    context: str = ""
) -> Dict[str, Any]:
    """
    Enhance a video clip with Gemini analysis and intelligent shot matching
    
    Args:
        video_path: Path to the video file
        shotlist: Complete shotlist dictionary with all shots and header
        clip_id: Identifier for the clip
        context: Additional context
        
    Returns:
        Dictionary containing enhanced metadata with matched shot numbers and dateline info
    """
    try:
        # Verify file exists
        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Read video file
        with open(video_path, 'rb') as f:
            video_data = f.read()
        
        file_size_mb = len(video_data) / 1024 / 1024
        logging.info(f"Processing clip {clip_id}: {video_path} ({file_size_mb:.2f} MB)")
        
        # Check file size limit (Gemini has a ~20MB limit for video)
        if file_size_mb > 15:
            logging.warning(f"Clip {clip_id} is large ({file_size_mb:.2f} MB), may fail")
        
        # Determine MIME type
        file_ext = Path(video_path).suffix.lower()
        mime_type_map = {
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska'
        }
        mime_type = mime_type_map.get(file_ext, 'video/mp4')
        
        # Create video part
        video_part = Part.from_data(data=video_data, mime_type=mime_type)
        
        # Build prompt with full shotlist
        prompt = self._build_prompt(shotlist, clip_id, context)
        
        # Generate content
        generation_config = {
            "temperature": 0.4,
            "top_p": 0.5,
            "top_k": 20,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        
        logging.info(f"Sending clip {clip_id} to Gemini for analysis...")
        
        # Try with retry logic for broken pipe and connection errors
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    [prompt, video_part],
                    generation_config=generation_config
                )
                
                # Extract JSON from response
                response_text = response.text
                logging.info(f"Received response for clip {clip_id}")
                break
                
            except (BrokenPipeError, ConnectionError, OSError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    import time
                    wait_time = (attempt + 1) * 2  # 2, 4, 6 seconds
                    logging.warning(f"Connection error for clip {clip_id} (attempt {attempt + 1}/{max_retries}): {e}")
                    logging.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Failed after {max_retries} attempts for clip {clip_id}: {e}")
                    raise
        
        # Parse JSON response
        try:
            # Try to extract JSON from markdown code blocks if present
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                json_str = response_text[json_start:json_end].strip()
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()
            
            result = json.loads(json_str)
            
            # Ensure required fields are present
            if 'clip_id' not in result:
                result['clip_id'] = clip_id
            if 'matched_shot_numbers' not in result:
                result['matched_shot_numbers'] = []
            if 'is_slate' not in result:
                result['is_slate'] = False
            if 'is_part_of_various' not in result:
                result['is_part_of_various'] = False
            
            # Add dateline metadata from matched shot(s)
            matched_nums = result.get('matched_shot_numbers', [])
            if matched_nums:
                shots = shotlist.get('shots', [])
                for shot in shots:
                    if shot.get('number') in matched_nums:
                        result['location'] = shot.get('location', '')
                        result['date'] = shot.get('date', '')
                        result['source'] = shot.get('source', '')
                        result['restrictions'] = shot.get('restrictions', '')
                        break
            else:
                # Fallback to header if no match
                header = shotlist.get('header', {})
                result['location'] = header.get('location', '')
                result['date'] = header.get('date', '')
                result['source'] = header.get('source', '')
                result['restrictions'] = header.get('restrictions', '')
            
            logging.info(f"Successfully enhanced clip {clip_id}")
            return result
            
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON response for clip {clip_id}: {e}")
            logging.error(f"Response text: {response_text}")
            
            # Return a fallback response with header dateline metadata
            header = shotlist.get('header', {})
            return {
                'clip_id': clip_id,
                'matched_shot_numbers': [],
                'is_slate': False,
                'is_part_of_various': False,
                'original_description': 'Unknown',
                'enhanced_description': response_text,
                'location': header.get('location', ''),
                'date': header.get('date', ''),
                'source': header.get('source', ''),
                'restrictions': header.get('restrictions', ''),
                'error': 'Failed to parse structured response',
                'raw_response': response_text
            }
    
    except FileNotFoundError as e:
        logging.error(f"File not found for clip {clip_id}: {e}")
        raise
    
    except Exception as e:
        logging.error(f"Error enhancing clip {clip_id}: {e}")
        raise
```

---

## Integration with UGC App

### Application Initialization

```python
# app.py or main.py

import os
from dotenv import load_dotenv
from modules.auth import initialize_auth, get_auth_instance
from modules.gemini_enhancer import GeminiEnhancer

# Load environment variables
load_dotenv()

# Initialize authentication on app startup
def startup():
    """Initialize authentication when app starts"""
    try:
        workspace_id, model_name = initialize_auth()
        print(f"✓ Authentication successful")
        print(f"  Workspace: {workspace_id}")
        print(f"  Model: {model_name}")
        return True
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return False

# Create Gemini enhancer instance
def create_enhancer():
    """Create a GeminiEnhancer instance"""
    try:
        enhancer = GeminiEnhancer()
        return enhancer
    except RuntimeError as e:
        print(f"Error: {e}")
        print("Please ensure authentication is initialized first.")
        return None
```

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

app = FastAPI(title="UGC Video Metadata Generator")

# Global enhancer instance
enhancer: Optional[GeminiEnhancer] = None

@app.on_event("startup")
async def startup_event():
    """Initialize authentication and Gemini on startup"""
    global enhancer
    
    try:
        # Initialize TR authentication
        workspace_id, model_name = initialize_auth()
        logging.info(f"✓ TR Authentication successful - Workspace: {workspace_id}")
        
        # Create Gemini enhancer
        enhancer = GeminiEnhancer()
        logging.info("✓ Gemini Enhancer initialized")
        
    except Exception as e:
        logging.error(f"✗ Startup failed: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    auth = get_auth_instance()
    return {
        "status": "healthy",
        "workspace_id": auth.workspace_id,
        "model": auth.model_name,
        "gemini_ready": enhancer is not None
    }

@app.post("/api/v1/analyze-video")
async def analyze_video(
    video_path: str,
    shotlist: dict,
    clip_id: str,
    context: str = ""
):
    """Analyze a video clip and generate metadata"""
    if enhancer is None:
        raise HTTPException(
            status_code=503,
            detail="Gemini enhancer not initialized"
        )
    
    try:
        result = enhancer.enhance_clip(
            video_path=video_path,
            shotlist=shotlist,
            clip_id=clip_id,
            context=context
        )
        return JSONResponse(content=result)
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/refresh-token")
async def refresh_token():
    """Manually refresh the authentication token"""
    try:
        auth = get_auth_instance()
        new_token = auth.refresh_token()
        
        # Reinitialize Gemini with new token
        global enhancer
        enhancer = GeminiEnhancer()
        
        return {
            "status": "success",
            "message": "Token refreshed and Gemini reinitialized"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Token Management

### Token Lifecycle

```python
# Token expires after a certain period (check with TR platform)
# Implement automatic refresh before expiry

import time
from datetime import datetime, timedelta
from threading import Thread

class TokenRefreshManager:
    def __init__(self, refresh_interval_minutes: int = 50):
        """
        Initialize token refresh manager
        
        Args:
            refresh_interval_minutes: How often to refresh (default 50 min for 60 min tokens)
        """
        self.refresh_interval = refresh_interval_minutes * 60  # Convert to seconds
        self.running = False
        self.thread = None
    
    def start(self):
        """Start automatic token refresh"""
        self.running = True
        self.thread = Thread(target=self._refresh_loop, daemon=True)
        self.thread.start()
        logging.info(f"Token refresh manager started (interval: {self.refresh_interval}s)")
    
    def stop(self):
        """Stop automatic token refresh"""
        self.running = False
        if self.thread:
            self.thread.join()
        logging.info("Token refresh manager stopped")
    
    def _refresh_loop(self):
        """Background loop to refresh token"""
        while self.running:
            time.sleep(self.refresh_interval)
            
            try:
                auth = get_auth_instance()
                auth.refresh_token()
                logging.info(f"✓ Token refreshed at {datetime.now()}")
                
                # Reinitialize Gemini with new credentials
                global enhancer
                enhancer = GeminiEnhancer()
                logging.info("✓ Gemini reinitialized with new token")
                
            except Exception as e:
                logging.error(f"✗ Token refresh failed: {e}")

# Usage in app
refresh_manager = TokenRefreshManager(refresh_interval_minutes=50)

@app.on_event("startup")
async def startup_event():
    # ... existing startup code ...
    refresh_manager.start()

@app.on_event("shutdown")
async def shutdown_event():
    refresh_manager.stop()
```

---

## Error Handling

### Authentication Errors

```python
class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass

class TokenExpiredError(Exception):
    """Raised when token has expired"""
    pass

class WorkspaceError(Exception):
    """Raised when workspace configuration is invalid"""
    pass

# In auth.py
def get_token(self) -> str:
    """Get authentication token with comprehensive error handling"""
    try:
        payload = {
            'workspace_id': self.workspace_id,
            'model_name': self.model_name
        }
        
        response = requests.post(
            self.credentials_url,
            json=payload,
            timeout=10
        )
        
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
        
        return self._token
        
    except requests.exceptions.Timeout:
        raise AuthenticationError("Authentication service timeout")
    except requests.exceptions.ConnectionError:
        raise AuthenticationError("Cannot connect to authentication service")
    except requests.exceptions.RequestException as e:
        raise AuthenticationError(f"Failed to retrieve authentication token: {e}")
```

### Vertex AI Errors

```python
# In gemini_enhancer.py

def _initialize_vertex(self):
    """Initialize Vertex AI with comprehensive error handling"""
    try:
        creds_data = self.auth.get_credentials()
        
        if not creds_data.get('token'):
            raise ValueError("No authentication token available")
        if not creds_data.get('project_id'):
            raise ValueError("No project_id in credentials")
        if not creds_data.get('region'):
            raise ValueError("No region in credentials")
        
        temp_creds = OAuth2Credentials(creds_data['token'])
        
        vertexai.init(
            project=creds_data['project_id'],
            location=creds_data['region'],
            credentials=temp_creds
        )
        
        system_instruction = self._load_system_instruction()
        
        self.model = GenerativeModel(
            model_name=self.auth.model_name,
            system_instruction=system_instruction
        )
        
        logging.info("✓ Vertex AI initialized successfully")
        
    except ValueError as e:
        logging.error(f"✗ Invalid credentials: {e}")
        raise
    except Exception as e:
        logging.error(f"✗ Error initializing Vertex AI: {e}")
        raise RuntimeError(f"Vertex AI initialization failed: {e}")
```

---

## Security Best Practices

### Environment Variables

```python
# Never commit .env files to version control
# .gitignore
.env
.env.local
.env.production
*.key
credentials.json

# Use different environments
# .env.development
WORKSPACE_ID=dev-workspace
MODEL_NAME=gemini-2.0-flash-exp
CREDENTIALS_URL=https://dev-auth.tr.com/api/token

# .env.production
WORKSPACE_ID=prod-workspace
MODEL_NAME=gemini-2.0-flash-exp
CREDENTIALS_URL=https://auth.tr.com/api/token
```

### Secrets Management

```python
# For production, use secrets management services

# AWS Secrets Manager
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name: str, region: str = "us-east-1"):
    """Retrieve secret from AWS Secrets Manager"""
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region
    )
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except ClientError as e:
        raise Exception(f"Failed to retrieve secret: {e}")

# Usage
secrets = get_secret("tr-ugc-app-credentials")
os.environ['WORKSPACE_ID'] = secrets['workspace_id']
os.environ['CREDENTIALS_URL'] = secrets['credentials_url']
```

### Token Security

```python
# Never log tokens
def safe_log_auth():
    """Log authentication info without exposing tokens"""
    auth = get_auth_instance()
    logging.info(f"Workspace: {auth.workspace_id}")
    logging.info(f"Model: {auth.model_name}")
    logging.info(f"Token: {'*' * 20}")  # Masked
    logging.info(f"Project: {auth.project_id}")
    logging.info(f"Region: {auth.region}")

# Store tokens securely in memory only
# Never write tokens to disk or logs
```

---

## Testing Authentication

### Unit Tests

```python
import unittest
from unittest.mock import patch, Mock
from modules.auth import ThomsonReutersAuth

class TestAuthentication(unittest.TestCase):
    
    @patch('requests.post')
    def test_get_token_success(self, mock_post):
        """Test successful token retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'token': 'test-token-123',
            'project_id': 'test-project',
            'region': 'us-central1'
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        auth = ThomsonReutersAuth()
        token = auth.get_token()
        
        self.assertEqual(token, 'test-token-123')
        self.assertEqual(auth.project_id, 'test-project')
        self.assertEqual(auth.region, 'us-central1')
    
    @patch('requests.post')
    def test_get_token_failure(self, mock_post):
        """Test token retrieval failure"""
        mock_post.side_effect = requests.exceptions.RequestException("Connection failed")
        
        auth = ThomsonReutersAuth()
        
        with self.assertRaises(Exception):
            auth.get_token()
    
    def test_missing_env_vars(self):
        """Test initialization with missing environment variables"""
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError):
                ThomsonReutersAuth()
```

### Integration Tests

```python
import pytest
from modules.auth import initialize_auth
from modules.gemini_enhancer import GeminiEnhancer

@pytest.fixture
def setup_auth():
    """Setup authentication for tests"""
    workspace_id, model_name = initialize_auth()
    return workspace_id, model_name

def test_auth_and_gemini_initialization(setup_auth):
    """Test full authentication and Gemini initialization"""
    workspace_id, model_name = setup_auth
    
    assert workspace_id is not None
    assert model_name == 'gemini-2.0-flash-exp'
    
    # Test Gemini enhancer creation
    enhancer = GeminiEnhancer()
    assert enhancer.model is not None
    assert enhancer.auth is not None

def test_token_refresh(setup_auth):
    """Test token refresh mechanism"""
    auth = get_auth_instance()
    
    old_token = auth._token
    new_token = auth.refresh_token()
    
    assert new_token != old_token
    assert auth._token == new_token
```

---

## Monitoring & Logging

### Authentication Monitoring

```python
import logging
from datetime import datetime

class AuthenticationLogger:
    """Enhanced logging for authentication events"""
    
    @staticmethod
    def log_token_request():
        logging.info(f"[AUTH] Token request initiated at {datetime.now()}")
    
    @staticmethod
    def log_token_success(workspace_id: str):
        logging.info(f"[AUTH] ✓ Token obtained successfully for workspace: {workspace_id}")
    
    @staticmethod
    def log_token_failure(error: str):
        logging.error(f"[AUTH] ✗ Token request failed: {error}")
    
    @staticmethod
    def log_token_refresh():
        logging.info(f"[AUTH] Token refresh initiated at {datetime.now()}")
    
    @staticmethod
    def log_vertex_init_success(project: str, region: str):
        logging.info(f"[VERTEX] ✓ Initialized - Project: {project}, Region: {region}")
    
    @staticmethod
    def log_vertex_init_failure(error: str):
        logging.error(f"[VERTEX] ✗ Initialization failed: {error}")

# Usage in auth.py
def get_token(self) -> str:
    AuthenticationLogger.log_token_request()
    try:
        # ... token retrieval code ...
        AuthenticationLogger.log_token_success(self.workspace_id)
        return self._token
    except Exception as e:
        AuthenticationLogger.log_token_failure(str(e))
        raise
```

### Metrics Collection

```python
from prometheus_client import Counter, Histogram
import time

# Define metrics
auth_requests = Counter('auth_requests_total', 'Total authentication requests')
auth_failures = Counter('auth_failures_total', 'Total authentication failures')
auth_duration = Histogram('auth_request_duration_seconds', 'Authentication request duration')
token_refreshes = Counter('token_refreshes_total', 'Total token refreshes')

def get_token_with_metrics(self) -> str:
    """Get token with metrics collection"""
    auth_requests.inc()
    start_time = time.time()
    
    try:
        token = self._get_token_internal()
        auth_duration.observe(time.time() - start_time)
        return token
    except Exception as e:
        auth_failures.inc()
        raise
```

---

## Configuration Management

### Multi-Environment Setup

```python
# config.py

from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Thomson Reuters Auth
    workspace_id: str
    model_name: str = "gemini-2.0-flash-exp"
    credentials_url: str
    
    # Application
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    
    # Token Management
    token_refresh_interval_minutes: int = 50
    token_timeout_seconds: int = 10
    
    # Gemini Configuration
    gemini_temperature: float = 0.4
    gemini_top_p: float = 0.5
    gemini_top_k: int = 20
    gemini_max_output_tokens: int = 8192
    gemini_max_retries: int = 3
    gemini_retry_delay_seconds: int = 5
    
    # File Upload
    max_file_size_mb: int = 500
    allowed_video_formats: list = ['.mp4', '.mov', '.avi', '.mkv']
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = Settings()

# Usage in auth.py
def __init__(self, config: Optional[Settings] = None):
    """Initialize with optional config"""
    self.config = config or settings
    self.workspace_id = self.config.workspace_id
    self.model_name = self.config.model_name
    self.credentials_url = self.config.credentials_url
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Environment variables configured
- [ ] Secrets management setup (if production)
- [ ] Token refresh manager enabled
- [ ] Logging configured properly
- [ ] Metrics collection enabled
- [ ] Health check endpoint tested
- [ ] Authentication tested with production credentials
- [ ] Gemini model access verified
- [ ] Error handling tested
- [ ] Rate limiting configured

### Post-Deployment

- [ ] Monitor authentication success rate
- [ ] Check token refresh frequency
- [ ] Verify Gemini API call success rate
- [ ] Review error logs
- [ ] Test failover scenarios
- [ ] Verify backup authentication method (if applicable)

---

## Troubleshooting Guide

### Common Issues

**Issue: "WORKSPACE_ID not found in environment variables"**
```
Solution:
1. Check .env file exists
2. Verify variable name is correct (all caps)
3. Restart application to reload environment
```

**Issue: "Failed to retrieve authentication token"**
```
Solution:
1. Check CREDENTIALS_URL is correct
2. Verify network connectivity
3. Check workspace credentials are valid
4. Review TR platform status
```

**Issue: "Error initializing Vertex AI"**
```
Solution:
1. Verify token is valid (not expired)
2. Check project_id and region in credentials
3. Verify Gemini model access permissions
4. Try refreshing token manually
```

**Issue: "BrokenPipeError during video analysis"**
```
Solution:
1. Already handled with retry logic (3 attempts)
2. Check video file size (< 15MB recommended)
3. Verify network stability
4. Increase retry delay if frequent
```

**Issue: "Token refresh not working"**
```
Solution:
1. Check TokenRefreshManager is started
2. Verify refresh interval is appropriate
3. Check credentials_url is accessible
4. Review refresh manager logs
```

---

## API Reference

### Authentication Endpoints

```python
POST /api/v1/auth/token
Description: Get new authentication token
Response: {
    "token": "string",
    "project_id": "string",
    "region": "string",
    "expires_at": "datetime"
}

POST /api/v1/auth/refresh
Description: Refresh existing token
Response: {
    "status": "success",
    "message": "Token refreshed"
}

GET /api/v1/auth/status
Description: Check authentication status
Response: {
    "authenticated": true,
    "workspace_id": "string",
    "model": "string",
    "token_valid": true
}
```

### Gemini Endpoints

```python
POST /api/v1/gemini/analyze
Description: Analyze video with Gemini
Request: {
    "video_path": "string",
    "shotlist": {},
    "clip_id": "string",
    "context": "string"
}
Response: {
    "clip_id": "string",
    "matched_shot_numbers": [int],
    "enhanced_description": "string",
    ...
}

GET /api/v1/gemini/health
Description: Check Gemini service health
Response: {
    "status": "healthy",
    "model": "string",
    "initialized": true
}
```

---

## Summary

The Thomson Reuters authentication system provides:

1. **Centralized Authentication**: Single point for managing Gemini access
2. **Token Management**: Automatic refresh and lifecycle management
3. **Security**: OAuth2 credentials with secure token handling
4. **Monitoring**: Comprehensive logging and metrics
5. **Reliability**: Retry logic and error handling
6. **Scalability**: Supports multiple workspaces and models

This architecture ensures secure, reliable access to Google Gemini while maintaining Thomson Reuters' security and compliance requirements.

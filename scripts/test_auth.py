#!/usr/bin/env python3
"""
Test script for Thomson Reuters Authentication

This script tests the authentication module by:
1. Loading environment variables
2. Initializing TR authentication
3. Retrieving a token
4. Getting full credentials
5. Testing token age tracking

Usage:
    python scripts/test_auth.py
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.auth import initialize_auth, get_auth_instance, safe_log_auth


def main():
    """Main test function"""
    print("=" * 70)
    print("Thomson Reuters Authentication Test")
    print("=" * 70)
    print()
    
    try:
        # Step 1: Initialize authentication
        print("Step 1: Initializing authentication...")
        workspace_id, model_name = initialize_auth()
        print(f"✓ Authentication initialized successfully")
        print(f"  Workspace ID: {workspace_id}")
        print(f"  Model Name: {model_name}")
        print()
        
        # Step 2: Get auth instance
        print("Step 2: Getting authentication instance...")
        auth = get_auth_instance()
        print(f"✓ Auth instance retrieved")
        print()
        
        # Step 3: Get credentials
        print("Step 3: Retrieving full credentials...")
        creds = auth.get_credentials()
        print(f"✓ Credentials retrieved successfully")
        print(f"  Token: {'*' * 20} (masked for security)")
        print(f"  Project ID: {creds['project_id']}")
        print(f"  Region: {creds['region']}")
        print()
        
        # Step 4: Check token validity
        print("Step 4: Checking token validity...")
        is_valid = auth.is_token_valid()
        print(f"✓ Token is valid: {is_valid}")
        print()
        
        # Step 5: Get token age
        print("Step 5: Checking token age...")
        token_age = auth.get_token_age_minutes()
        if token_age is not None:
            print(f"✓ Token age: {token_age:.2f} minutes")
        else:
            print("✗ Token age not available")
        print()
        
        # Step 6: Display full auth status
        print("Step 6: Full authentication status...")
        safe_log_auth()
        print()
        
        print("=" * 70)
        print("✓ All authentication tests passed successfully!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. The authentication module is working correctly")
        print("  2. You can now proceed to implement the Gemini enhancer")
        print("  3. Token will be automatically refreshed every 50 minutes")
        print()
        
        return 0
        
    except ValueError as e:
        print(f"\n✗ Configuration Error: {e}")
        print("\nPlease ensure your .env file contains:")
        print("  - WORKSPACE_ID")
        print("  - CREDENTIALS_URL")
        print("  - MODEL_NAME (optional, defaults to gemini-2.0-flash-exp)")
        return 1
        
    except Exception as e:
        print(f"\n✗ Authentication Test Failed: {e}")
        print(f"\nError type: {type(e).__name__}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

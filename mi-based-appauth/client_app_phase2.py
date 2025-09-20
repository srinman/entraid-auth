"""
Client Application with Pure Managed Identity Authentication
Demonstrates calling API using managed identity tokens directly
"""

import asyncio
import aiohttp
import json
import os
from azure.identity.aio import DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError

class ManagedIdentityAPIClient:
    def __init__(self):
        self.api_base_url = os.environ.get('API_BASE_URL', 'http://api-service:8000')
        # For managed identity, we typically request tokens for Azure management scope
        self.token_scope = "https://management.azure.com/.default"
        self.credential = DefaultAzureCredential()
        self.token_cache = {}
        
    async def get_managed_identity_token(self):
        """
        Get managed identity token for authentication
        """
        try:
            # Check cache first (tokens are valid for 24 hours)
            if 'access_token' in self.token_cache:
                return self.token_cache['access_token']
            
            # Get token using managed identity
            token = await self.credential.get_token(self.token_scope)
            
            # Cache the token
            self.token_cache['access_token'] = token.token
            
            print(f"Acquired new managed identity token (expires: {token.expires_on})")
            return token.token
            
        except ClientAuthenticationError as e:
            print(f"Managed identity authentication failed: {e}")
            raise
        except Exception as e:
            print(f"Token acquisition failed: {e}")
            raise
    
    async def make_authenticated_request(self, method, endpoint, data=None):
        """
        Make authenticated API request using managed identity
        """
        try:
            token = await self.get_managed_identity_token()
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'User-Agent': 'ManagedIdentityClient/1.0'
            }
            
            url = f"{self.api_base_url}{endpoint}"
            
            async with aiohttp.ClientSession() as session:
                if method.upper() == 'GET':
                    async with session.get(url, headers=headers) as response:
                        return await self.handle_response(response)
                elif method.upper() == 'POST':
                    async with session.post(url, headers=headers, json=data) as response:
                        return await self.handle_response(response)
                elif method.upper() == 'PUT':
                    async with session.put(url, headers=headers, json=data) as response:
                        return await self.handle_response(response)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                    
        except Exception as e:
            print(f"API request failed: {e}")
            raise
    
    async def handle_response(self, response):
        """
        Handle API response with improved error handling
        """
        try:
            response_text = await response.text()
            
            if response.status == 200 or response.status == 201:
                return json.loads(response_text) if response_text else {}
            elif response.status == 401:
                # Clear token cache and provide clear error
                self.token_cache.clear()
                error_detail = json.loads(response_text) if response_text else {}
                raise Exception(f"Authentication failed: {error_detail.get('error', 'Invalid or expired token')}")
            elif response.status == 403:
                error_detail = json.loads(response_text) if response_text else {}
                raise Exception(f"Authorization failed: {error_detail.get('error', 'Insufficient permissions')}")
            else:
                error_detail = json.loads(response_text) if response_text else {}
                raise Exception(f"API request failed with status {response.status}: {error_detail}")
                
        except json.JSONDecodeError:
            raise Exception(f"API request failed with status {response.status}: {response_text}")

class PlanManagerV2:
    def __init__(self):
        self.client = ManagedIdentityAPIClient()
    
    async def list_plans(self):
        """List all plans (permission: read on plans)"""
        try:
            result = await self.client.make_authenticated_request('GET', '/api/plans')
            print("Plans retrieved successfully:")
            print(json.dumps(result, indent=2))
            return result
        except Exception as e:
            print(f"Failed to list plans: {e}")
            return None
    
    async def create_plan(self, plan_name):
        """Create a new plan (permission: create on plans)"""
        try:
            plan_data = {'name': plan_name}
            result = await self.client.make_authenticated_request('POST', '/api/plans', plan_data)
            print("Plan created successfully:")
            print(json.dumps(result, indent=2))
            return result
        except Exception as e:
            print(f"Failed to create plan: {e}")
            return None

class AccountManagerV2:
    def __init__(self):
        self.client = ManagedIdentityAPIClient()
    
    async def list_accounts(self):
        """List all accounts (permission: read on accounts)"""
        try:
            result = await self.client.make_authenticated_request('GET', '/api/accounts')
            print("Accounts retrieved successfully:")
            print(json.dumps(result, indent=2))
            return result
        except Exception as e:
            print(f"Failed to list accounts: {e}")
            return None
    
    async def update_account_settings(self, account_id, settings):
        """Update account settings (permission: update on accounts)"""
        try:
            result = await self.client.make_authenticated_request(
                'PUT', 
                f'/api/accounts/{account_id}/settings', 
                settings
            )
            print("Account settings updated successfully:")
            print(json.dumps(result, indent=2))
            return result
        except Exception as e:
            print(f"Failed to update account settings: {e}")
            return None
    
    async def get_permissions(self):
        """Get current user's permissions"""
        try:
            result = await self.client.make_authenticated_request('GET', '/api/user/permissions')
            print("User permissions retrieved:")
            print(json.dumps(result, indent=2))
            return result
        except Exception as e:
            print(f"Failed to get permissions: {e}")
            return None

async def demonstrate_managed_identity_auth():
    """
    Demonstrate API calls using pure managed identity authentication
    """
    print("=== Client App Demo - Phase 2 (Managed Identity + PlainID) ===")
    print("Authentication: Managed Identity")
    print("Authorization: PlainID Fine-grained Permissions")
    
    plan_manager = PlanManagerV2()
    account_manager = AccountManagerV2()
    
    # Get user permissions first
    print("\n1. Getting User Permissions:")
    await account_manager.get_permissions()
    
    # Test plan operations
    print("\n2. Testing Plan Operations:")
    await plan_manager.list_plans()
    await plan_manager.create_plan("Strategic Plan 2025 - MI Version")
    
    # Test account operations  
    print("\n3. Testing Account Operations:")
    await account_manager.list_accounts()
    await account_manager.update_account_settings(1, {
        'notification_enabled': True,
        'theme': 'dark',
        'auto_backup': True
    })

async def test_health_endpoint():
    """Test the health endpoint (no authentication required)"""
    try:
        client = ManagedIdentityAPIClient()
        url = f"{client.api_base_url}/health"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    print("Health check passed:")
                    print(json.dumps(result, indent=2))
                else:
                    print(f"Health check failed: {response.status}")
    except Exception as e:
        print(f"Health check error: {e}")

async def main():
    """Main execution function for Phase 2 demo"""
    
    # Check environment variables
    required_env_vars = ['AZURE_TENANT_ID', 'AZURE_CLIENT_ID']
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"Missing required environment variables: {missing_vars}")
        print("Please set the following environment variables:")
        for var in missing_vars:
            print(f"  export {var}=<value>")
        return
    
    try:
        # Test health endpoint first
        print("Testing health endpoint...")
        await test_health_endpoint()
        
        print("\n" + "="*60)
        
        # Run the demonstration
        await demonstrate_managed_identity_auth()
        
        print("\n" + "="*60)
        print("Demo completed successfully!")
        print("\nKey differences from Phase 1:")
        print("✓ No app registration required")
        print("✓ Direct managed identity authentication") 
        print("✓ Fine-grained authorization via PlainID")
        print("✓ Reduced security team dependencies")
        print("✓ Simplified token management")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
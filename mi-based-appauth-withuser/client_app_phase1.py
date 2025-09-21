"""
Client Application with Workload Identity Authentication
Demonstrates calling API using app registration tokens via workload identity
"""

import asyncio
import aiohttp
import json
import os
from azure.identity.aio import DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError

class APIClient:
    def __init__(self):
        self.api_base_url = os.environ.get('API_BASE_URL', 'http://api-service:8000')
        self.api_scope = os.environ.get('API_SCOPE')  # e.g., "api://your-api-app-id/.default"
        self.credential = DefaultAzureCredential()
        self.token_cache = {}
        
    async def get_access_token(self):
        """
        Get access token for API using workload identity
        """
        try:
            # Check cache first (tokens are valid for 24 hours)
            if 'access_token' in self.token_cache:
                return self.token_cache['access_token']
            
            # Get token using managed identity via workload identity
            token = await self.credential.get_token(self.api_scope)
            
            # Cache the token
            self.token_cache['access_token'] = token.token
            
            return token.token
            
        except ClientAuthenticationError as e:
            print(f"Authentication failed: {e}")
            raise
        except Exception as e:
            print(f"Token acquisition failed: {e}")
            raise
    
    async def make_authenticated_request(self, method, endpoint, data=None):
        """
        Make authenticated API request
        """
        try:
            token = await self.get_access_token()
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
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
        Handle API response
        """
        if response.status == 200 or response.status == 201:
            return await response.json()
        elif response.status == 401:
            # Clear token cache and retry once
            self.token_cache.clear()
            raise Exception("Authentication failed - token may be expired")
        elif response.status == 403:
            error_detail = await response.text()
            raise Exception(f"Authorization failed: {error_detail}")
        else:
            error_detail = await response.text()
            raise Exception(f"API request failed with status {response.status}: {error_detail}")

class PlanManager:
    def __init__(self):
        self.client = APIClient()
    
    async def list_plans(self):
        """List all plans (requires planadmin or accountviewer role)"""
        try:
            result = await self.client.make_authenticated_request('GET', '/api/plans')
            print("Plans retrieved successfully:")
            print(json.dumps(result, indent=2))
            return result
        except Exception as e:
            print(f"Failed to list plans: {e}")
            return None
    
    async def create_plan(self, plan_name):
        """Create a new plan (requires planadmin role)"""
        try:
            plan_data = {'name': plan_name}
            result = await self.client.make_authenticated_request('POST', '/api/plans', plan_data)
            print("Plan created successfully:")
            print(json.dumps(result, indent=2))
            return result
        except Exception as e:
            print(f"Failed to create plan: {e}")
            return None

class AccountManager:
    def __init__(self):
        self.client = APIClient()
    
    async def list_accounts(self):
        """List all accounts (requires accountviewer or accountadmin role)"""
        try:
            result = await self.client.make_authenticated_request('GET', '/api/accounts')
            print("Accounts retrieved successfully:")
            print(json.dumps(result, indent=2))
            return result
        except Exception as e:
            print(f"Failed to list accounts: {e}")
            return None
    
    async def update_account_settings(self, account_id, settings):
        """Update account settings (requires accountadmin role)"""
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

async def demonstrate_api_calls():
    """
    Demonstrate various API calls with different role requirements
    """
    print("=== Client App Demo - Phase 1 (App Registration) ===")
    
    plan_manager = PlanManager()
    account_manager = AccountManager()
    
    # Test plan operations
    print("\n1. Testing Plan Operations:")
    await plan_manager.list_plans()
    await plan_manager.create_plan("Demo Plan from Client")
    
    # Test account operations  
    print("\n2. Testing Account Operations:")
    await account_manager.list_accounts()
    await account_manager.update_account_settings(1, {
        'notification_enabled': True,
        'theme': 'dark'
    })

async def test_health_endpoint():
    """Test the health endpoint (no authentication required)"""
    try:
        client = APIClient()
        # Override to make unauthenticated request
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
    """Main execution function"""
    
    # Check environment variables
    required_env_vars = ['API_SCOPE', 'AZURE_TENANT_ID', 'AZURE_CLIENT_ID']
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
        
        print("\n" + "="*50)
        
        # Run the demonstration
        await demonstrate_api_calls()
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
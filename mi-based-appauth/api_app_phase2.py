"""
API Application with Managed Identity and PlainID Integration
Demonstrates pure managed identity authentication with external authorization
"""

from flask import Flask, request, jsonify
from azure.identity import DefaultAzureCredential
import jwt
import requests
import os
from functools import wraps
import json

app = Flask(__name__)

# Configuration
TENANT_ID = os.environ.get('AZURE_TENANT_ID')
CLIENT_ID = os.environ.get('AZURE_CLIENT_ID')  # Managed Identity client ID
PLAINID_ENDPOINT = os.environ.get('PLAINID_ENDPOINT', 'https://your-plainid-instance.com/api/v1')
PLAINID_TOKEN = os.environ.get('PLAINID_TOKEN')

class ManagedIdentityAuth:
    def __init__(self):
        self.tenant_id = TENANT_ID
        self.client_id = CLIENT_ID
        self.credential = DefaultAzureCredential()
        
    def validate_managed_identity_token(self, token):
        """
        Validate managed identity token
        Returns the token payload if valid, None otherwise
        """
        try:
            # Get Azure AD public keys for token validation
            jwks_url = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"
            jwks_response = requests.get(jwks_url)
            jwks = jwks_response.json()
            
            # Decode header to find key
            header = jwt.get_unverified_header(token)
            
            # Find the correct key
            key = None
            for jwk in jwks['keys']:
                if jwk['kid'] == header['kid']:
                    key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
                    break
            
            if not key:
                return None
            
            # Validate token for managed identity
            # Note: Managed identity tokens use different audience
            payload = jwt.decode(
                token,
                key,
                algorithms=['RS256'],
                audience="https://management.azure.com/",  # Standard MI audience
                issuer=f"https://sts.windows.net/{self.tenant_id}/"
            )
            
            # Verify this is a managed identity token
            if payload.get('idtyp') != 'MI':
                return None
                
            return payload
            
        except Exception as e:
            print(f"Token validation error: {e}")
            return None

class PlainIDAuthorizer:
    def __init__(self):
        self.endpoint = PLAINID_ENDPOINT
        self.token = PLAINID_TOKEN
        
    def check_permission(self, user_id, resource, action, context=None):
        """
        Check permission using PlainID
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'user': user_id,
                'resource': resource,
                'action': action,
                'context': context or {}
            }
            
            response = requests.post(
                f"{self.endpoint}/authorize",
                headers=headers,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('decision') == 'Permit'
            else:
                # Fail secure - deny if PlainID is unavailable
                print(f"PlainID authorization failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"PlainID authorization error: {e}")
            # Fail secure - deny if there's an error
            return False
    
    def get_user_permissions(self, user_id):
        """
        Get all permissions for a user from PlainID
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.endpoint}/permissions/{user_id}",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
                
        except Exception as e:
            print(f"PlainID permissions query error: {e}")
            return {}

# Initialize auth components
auth_validator = ManagedIdentityAuth()
plainid_authorizer = PlainIDAuthorizer()

def require_permission(resource, action):
    """
    Decorator to require specific permission for API endpoints using PlainID
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Authorization header required'}), 401
            
            token = auth_header.split(' ')[1]
            
            # Validate managed identity token
            payload = auth_validator.validate_managed_identity_token(token)
            
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            # Extract user identity (managed identity principal ID)
            user_id = payload.get('oid')  # Object ID of the managed identity
            
            if not user_id:
                return jsonify({'error': 'Invalid token - missing user identity'}), 401
            
            # Check permission using PlainID
            context = {
                'client_id': payload.get('appid'),
                'tenant_id': payload.get('tid'),
                'request_path': request.path,
                'request_method': request.method
            }
            
            has_permission = plainid_authorizer.check_permission(
                user_id, resource, action, context
            )
            
            if not has_permission:
                return jsonify({
                    'error': f'Access denied. Required permission: {action} on {resource}'
                }), 403
            
            # Add user info to request context
            request.token_payload = payload
            request.user_id = user_id
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# API Endpoints

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint - no authentication required"""
    return jsonify({'status': 'healthy', 'auth_mode': 'managed_identity_plainid'})

@app.route('/api/plans', methods=['GET'])
@require_permission('plans', 'read')
def get_plans():
    """Get plans - permission checked via PlainID"""
    user_info = getattr(request, 'token_payload', {})
    user_id = getattr(request, 'user_id', '')
    
    # Get user's permissions for transparency
    user_permissions = plainid_authorizer.get_user_permissions(user_id)
    
    return jsonify({
        'plans': [
            {'id': 1, 'name': 'Strategic Plan 2024', 'status': 'active'},
            {'id': 2, 'name': 'Operational Plan Q1', 'status': 'draft'}
        ],
        'user': {
            'managed_identity_id': user_info.get('oid'),
            'client_id': user_info.get('appid'),
            'permissions': user_permissions
        }
    })

@app.route('/api/plans', methods=['POST'])
@require_permission('plans', 'create')
def create_plan():
    """Create plan - permission checked via PlainID"""
    plan_data = request.get_json()
    user_info = getattr(request, 'token_payload', {})
    user_id = getattr(request, 'user_id', '')
    
    return jsonify({
        'message': 'Plan created successfully',
        'plan': {
            'id': 3,
            'name': plan_data.get('name', 'New Plan'),
            'created_by': user_id,
            'status': 'draft'
        }
    }), 201

@app.route('/api/accounts', methods=['GET'])
@require_permission('accounts', 'read')
def get_accounts():
    """Get accounts - permission checked via PlainID"""
    user_info = getattr(request, 'token_payload', {})
    user_id = getattr(request, 'user_id', '')
    
    return jsonify({
        'accounts': [
            {'id': 1, 'name': 'Account A', 'status': 'active'},
            {'id': 2, 'name': 'Account B', 'status': 'inactive'}
        ],
        'user': {
            'managed_identity_id': user_id,
            'client_id': user_info.get('appid')
        }
    })

@app.route('/api/accounts/<int:account_id>/settings', methods=['PUT'])
@require_permission('accounts', 'update')
def update_account_settings(account_id):
    """Update account settings - permission checked via PlainID"""
    settings_data = request.get_json()
    user_info = getattr(request, 'token_payload', {})
    user_id = getattr(request, 'user_id', '')
    
    # Additional fine-grained check for specific account
    context = {'account_id': account_id}
    can_update_account = plainid_authorizer.check_permission(
        user_id, f'accounts/{account_id}', 'update', context
    )
    
    if not can_update_account:
        return jsonify({
            'error': f'Access denied for account {account_id}'
        }), 403
    
    return jsonify({
        'message': f'Account {account_id} settings updated',
        'settings': settings_data,
        'updated_by': user_id
    })

@app.route('/api/user/permissions', methods=['GET'])
@require_permission('user', 'read_permissions')
def get_user_permissions():
    """Get current user's permissions"""
    user_id = getattr(request, 'user_id', '')
    permissions = plainid_authorizer.get_user_permissions(user_id)
    
    return jsonify({
        'user_id': user_id,
        'permissions': permissions
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
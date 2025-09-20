"""
API Application with App Registration Role Validation
Demonstrates role-based authorization using Entra ID app registration roles
"""

from flask import Flask, request, jsonify
from azure.identity import DefaultAzureCredential
import jwt
import requests
import os
from functools import wraps

app = Flask(__name__)

# Configuration
TENANT_ID = os.environ.get('AZURE_TENANT_ID')
CLIENT_ID = os.environ.get('AZURE_CLIENT_ID')  # API app registration client ID

class AuthValidator:
    def __init__(self):
        self.tenant_id = TENANT_ID
        self.client_id = CLIENT_ID
        self.credential = DefaultAzureCredential()
        
    def validate_token_and_roles(self, token, required_roles):
        """
        Validate JWT token and check for required roles
        """
        try:
            # Get Azure AD public keys for token validation
            jwks_url = f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"
            jwks_response = requests.get(jwks_url)
            jwks = jwks_response.json()
            
            # Decode and validate token (simplified - use proper JWT validation in production)
            header = jwt.get_unverified_header(token)
            
            # Find the correct key
            key = None
            for jwk in jwks['keys']:
                if jwk['kid'] == header['kid']:
                    key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
                    break
            
            if not key:
                return False, "Invalid token - key not found"
            
            # Decode token
            payload = jwt.decode(
                token,
                key,
                algorithms=['RS256'],
                audience=f"api://{self.client_id}",
                issuer=f"https://sts.windows.net/{self.tenant_id}/"
            )
            
            # Check if token has required roles
            token_roles = payload.get('roles', [])
            
            # Check if any of the required roles are present
            if not any(role in token_roles for role in required_roles):
                return False, f"Insufficient permissions. Required: {required_roles}, Found: {token_roles}"
            
            return True, payload
            
        except jwt.ExpiredSignatureError:
            return False, "Token expired"
        except jwt.InvalidTokenError as e:
            return False, f"Invalid token: {str(e)}"
        except Exception as e:
            return False, f"Token validation error: {str(e)}"

auth_validator = AuthValidator()

def require_roles(*roles):
    """
    Decorator to require specific roles for API endpoints
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Authorization header required'}), 401
            
            token = auth_header.split(' ')[1]
            
            is_valid, result = auth_validator.validate_token_and_roles(token, roles)
            
            if not is_valid:
                return jsonify({'error': result}), 403
            
            # Add user info to request context
            request.token_payload = result
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# API Endpoints

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint - no authentication required"""
    return jsonify({'status': 'healthy'})

@app.route('/api/plans', methods=['GET'])
@require_roles('planadmin', 'accountviewer')
def get_plans():
    """Get plans - requires planadmin or accountviewer role"""
    user_info = getattr(request, 'token_payload', {})
    return jsonify({
        'plans': [
            {'id': 1, 'name': 'Strategic Plan 2024'},
            {'id': 2, 'name': 'Operational Plan Q1'}
        ],
        'user': {
            'sub': user_info.get('sub'),
            'roles': user_info.get('roles', [])
        }
    })

@app.route('/api/plans', methods=['POST'])
@require_roles('planadmin')
def create_plan():
    """Create plan - requires planadmin role"""
    plan_data = request.get_json()
    user_info = getattr(request, 'token_payload', {})
    
    return jsonify({
        'message': 'Plan created successfully',
        'plan': {
            'id': 3,
            'name': plan_data.get('name', 'New Plan'),
            'created_by': user_info.get('sub')
        }
    }), 201

@app.route('/api/accounts', methods=['GET'])
@require_roles('accountviewer', 'accountadmin')
def get_accounts():
    """Get accounts - requires accountviewer or accountadmin role"""
    user_info = getattr(request, 'token_payload', {})
    return jsonify({
        'accounts': [
            {'id': 1, 'name': 'Account A', 'status': 'active'},
            {'id': 2, 'name': 'Account B', 'status': 'inactive'}
        ],
        'user': {
            'sub': user_info.get('sub'),
            'roles': user_info.get('roles', [])
        }
    })

@app.route('/api/accounts/<int:account_id>/settings', methods=['PUT'])
@require_roles('accountadmin')
def update_account_settings(account_id):
    """Update account settings - requires accountadmin role"""
    settings_data = request.get_json()
    user_info = getattr(request, 'token_payload', {})
    
    return jsonify({
        'message': f'Account {account_id} settings updated',
        'settings': settings_data,
        'updated_by': user_info.get('sub')
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
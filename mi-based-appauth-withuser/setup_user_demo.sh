#!/bin/bash

# Setup script for User-Based Authorization Demo
# This script creates test users and assigns them to app roles

set -e

echo "🚀 Setting up User-Based Authorization Demo"
echo "==========================================="

# Configuration
TENANT_DOMAIN="company.com"  # Change this to your actual tenant domain
RESOURCE_GROUP="your-resource-group"  # Change this to your resource group
LOCATION="your-location"  # Change this to your location

# App names
API_APP_NAME="api-app-workload-identity-user"
CLIENT_APP_NAME="client-app-workload-identity-user"

echo "📋 Configuration:"
echo "  - Tenant Domain: $TENANT_DOMAIN"
echo "  - Resource Group: $RESOURCE_GROUP"
echo "  - Location: $LOCATION"
echo "  - API App: $API_APP_NAME"
echo "  - Client App: $CLIENT_APP_NAME"
echo ""

# Function to check if user exists
check_user_exists() {
    local user_email=$1
    if az ad user show --id "$user_email" >/dev/null 2>&1; then
        echo "✅ User $user_email already exists"
        return 0
    else
        echo "❌ User $user_email does not exist"
        return 1
    fi
}

# Function to create user if not exists
create_user_if_needed() {
    local username=$1
    local user_email="${username}@${TENANT_DOMAIN}"
    local display_name="Test User ${username#testuser}"
    
    if ! check_user_exists "$user_email"; then
        echo "🔧 Creating user: $user_email"
        # Note: In production, you'd use proper password and force password change
        az ad user create \
            --user-principal-name "$user_email" \
            --display-name "$display_name" \
            --mail-nickname "$username" \
            --password "TempPassword123!" \
            --force-change-password-next-sign-in true
        echo "✅ Created user: $user_email"
    fi
}

echo "👥 Step 1: Creating test users..."
echo "================================="

# Create test users
USERS=("testuser1" "testuser2" "testuser3" "testuser4" "testuser5" "testuser6")

for user in "${USERS[@]}"; do
    create_user_if_needed "$user"
done

echo ""
echo "📱 Step 2: Creating app registrations..."
echo "========================================"

# Create API app registration
echo "🔧 Creating API app registration..."
az ad app create \
    --display-name "$API_APP_NAME" \
    --sign-in-audience "AzureADMyOrg"

API_APP_ID=$(az ad app list --display-name "$API_APP_NAME" --query "[0].appId" -o tsv)
echo "✅ API App ID: $API_APP_ID"

# Create client app registration
echo "🔧 Creating client app registration..."
az ad app create \
    --display-name "$CLIENT_APP_NAME" \
    --sign-in-audience "AzureADMyOrg"

CLIENT_APP_ID=$(az ad app list --display-name "$CLIENT_APP_NAME" --query "[0].appId" -o tsv)
echo "✅ Client App ID: $CLIENT_APP_ID"

echo ""
echo "🎭 Step 3: Defining app roles..."
echo "==============================="

# Create app roles JSON
cat > app-roles.json << EOF
[
  {
    "allowedMemberTypes": ["User"],
    "description": "Plan administrators can manage all planning resources",
    "displayName": "Plan Admin",
    "id": "$(uuidgen)",
    "isEnabled": true,
    "value": "planadmin"
  },
  {
    "allowedMemberTypes": ["User"],
    "description": "Account viewers can read account information", 
    "displayName": "Account Viewer",
    "id": "$(uuidgen)",
    "isEnabled": true,
    "value": "accountviewer"
  },
  {
    "allowedMemberTypes": ["User"],
    "description": "Account administrators can manage account settings",
    "displayName": "Account Admin", 
    "id": "$(uuidgen)",
    "isEnabled": true,
    "value": "accountadmin"
  }
]
EOF

# Update API app with roles
echo "🔧 Adding app roles to API app..."
az ad app update --id $API_APP_ID --app-roles @app-roles.json
echo "✅ App roles added to API app"

echo ""
echo "🔗 Step 4: Creating service principals..."
echo "========================================"

# Create service principals
echo "🔧 Creating service principal for API app..."
az ad sp create --id $API_APP_ID

echo "🔧 Creating service principal for client app..."
az ad sp create --id $CLIENT_APP_ID

# Get service principal IDs
API_SP_ID=$(az ad sp show --id $API_APP_ID --query "id" -o tsv)
CLIENT_SP_ID=$(az ad sp show --id $CLIENT_APP_ID --query "id" -o tsv)

echo "✅ API Service Principal ID: $API_SP_ID"
echo "✅ Client Service Principal ID: $CLIENT_SP_ID"

echo ""
echo "🎯 Step 5: Assigning users to roles..."
echo "====================================="

# Get role IDs
PLAN_ADMIN_ROLE_ID=$(az ad app show --id $API_APP_ID --query "appRoles[?value=='planadmin'].id" -o tsv)
ACCOUNT_VIEWER_ROLE_ID=$(az ad app show --id $API_APP_ID --query "appRoles[?value=='accountviewer'].id" -o tsv) 
ACCOUNT_ADMIN_ROLE_ID=$(az ad app show --id $API_APP_ID --query "appRoles[?value=='accountadmin'].id" -o tsv)

echo "📋 Role IDs:"
echo "  - Plan Admin: $PLAN_ADMIN_ROLE_ID"
echo "  - Account Viewer: $ACCOUNT_VIEWER_ROLE_ID"
echo "  - Account Admin: $ACCOUNT_ADMIN_ROLE_ID"

# Get user object IDs
TESTUSER1_ID=$(az ad user show --id "testuser1@$TENANT_DOMAIN" --query "id" -o tsv)
TESTUSER2_ID=$(az ad user show --id "testuser2@$TENANT_DOMAIN" --query "id" -o tsv)
TESTUSER3_ID=$(az ad user show --id "testuser3@$TENANT_DOMAIN" --query "id" -o tsv)
TESTUSER4_ID=$(az ad user show --id "testuser4@$TENANT_DOMAIN" --query "id" -o tsv)
TESTUSER5_ID=$(az ad user show --id "testuser5@$TENANT_DOMAIN" --query "id" -o tsv)
TESTUSER6_ID=$(az ad user show --id "testuser6@$TENANT_DOMAIN" --query "id" -o tsv)

# Assign users to roles
echo ""
echo "🔧 Assigning testuser1 to planadmin role..."
az ad app-role-assignment create \
    --app-role-id $PLAN_ADMIN_ROLE_ID \
    --principal-id $TESTUSER1_ID \
    --resource-id $API_SP_ID

echo "🔧 Assigning testuser2 to accountviewer role..."
az ad app-role-assignment create \
    --app-role-id $ACCOUNT_VIEWER_ROLE_ID \
    --principal-id $TESTUSER2_ID \
    --resource-id $API_SP_ID

echo "🔧 Assigning testuser3 to accountadmin role..."
az ad app-role-assignment create \
    --app-role-id $ACCOUNT_ADMIN_ROLE_ID \
    --principal-id $TESTUSER3_ID \
    --resource-id $API_SP_ID

echo "🔧 Assigning testuser4,5,6 to accountviewer role..."
for USER_ID in $TESTUSER4_ID $TESTUSER5_ID $TESTUSER6_ID; do
    az ad app-role-assignment create \
        --app-role-id $ACCOUNT_VIEWER_ROLE_ID \
        --principal-id $USER_ID \
        --resource-id $API_SP_ID
done

echo ""
echo "🏗️ Step 6: Creating managed identities..."
echo "========================================"

# Create managed identities for workload identity
echo "🔧 Creating managed identity for API workload..."
az identity create \
    --name "workload-identity-api-user" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION"

echo "🔧 Creating managed identity for client workload..."
az identity create \
    --name "workload-identity-client-user" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION"

# Get identity details
API_IDENTITY_CLIENT_ID=$(az identity show --name "workload-identity-api-user" --resource-group "$RESOURCE_GROUP" --query "clientId" -o tsv)
CLIENT_IDENTITY_CLIENT_ID=$(az identity show --name "workload-identity-client-user" --resource-group "$RESOURCE_GROUP" --query "clientId" -o tsv)

echo "✅ API Managed Identity Client ID: $API_IDENTITY_CLIENT_ID"
echo "✅ Client Managed Identity Client ID: $CLIENT_IDENTITY_CLIENT_ID"

echo ""
echo "📄 Step 7: Generating configuration files..."
echo "==========================================="

# Generate environment file
cat > .env << EOF
# App Registration IDs
API_APP_ID=$API_APP_ID
CLIENT_APP_ID=$CLIENT_APP_ID
API_SP_ID=$API_SP_ID
CLIENT_SP_ID=$CLIENT_SP_ID

# Role IDs
PLAN_ADMIN_ROLE_ID=$PLAN_ADMIN_ROLE_ID
ACCOUNT_VIEWER_ROLE_ID=$ACCOUNT_VIEWER_ROLE_ID
ACCOUNT_ADMIN_ROLE_ID=$ACCOUNT_ADMIN_ROLE_ID

# User IDs
TESTUSER1_ID=$TESTUSER1_ID
TESTUSER2_ID=$TESTUSER2_ID
TESTUSER3_ID=$TESTUSER3_ID
TESTUSER4_ID=$TESTUSER4_ID
TESTUSER5_ID=$TESTUSER5_ID
TESTUSER6_ID=$TESTUSER6_ID

# Managed Identity IDs
API_IDENTITY_CLIENT_ID=$API_IDENTITY_CLIENT_ID
CLIENT_IDENTITY_CLIENT_ID=$CLIENT_IDENTITY_CLIENT_ID

# Configuration
TENANT_DOMAIN=$TENANT_DOMAIN
RESOURCE_GROUP=$RESOURCE_GROUP
LOCATION=$LOCATION
EOF

echo "✅ Created .env file with all configuration"

# Generate user summary
cat > user_assignments.md << EOF
# User Role Assignments Summary

## Created Users and Roles

| User | Role | Permissions |
|------|------|-------------|
| testuser1@$TENANT_DOMAIN | planadmin | Full plan management |
| testuser2@$TENANT_DOMAIN | accountviewer | Read account information |
| testuser3@$TENANT_DOMAIN | accountadmin | Manage account settings |
| testuser4@$TENANT_DOMAIN | accountviewer | Read account information |
| testuser5@$TENANT_DOMAIN | accountviewer | Read account information |
| testuser6@$TENANT_DOMAIN | accountviewer | Read account information |

## Test Scenarios

### Phase 1 Testing (App Registration)
1. User signs in to client application
2. Client requests access token for API on behalf of user
3. Token contains user's assigned roles
4. API validates user identity and role claims

### Phase 2 Testing (Managed Identity + PlainID)
1. User signs in to client application  
2. Client uses managed identity to call API with user context
3. API queries PlainID with user identity
4. PlainID returns user-specific permissions

## Next Steps

1. **Configure AKS Workload Identity**: Set up federated credentials for managed identities
2. **Deploy Applications**: Deploy client and API applications to AKS
3. **Configure PlainID**: Set up user attribute mappings and policies
4. **Test User Flows**: Verify each user gets appropriate permissions

## Cleanup

To remove all created resources:
\`\`\`bash
./cleanup.sh
\`\`\`
EOF

echo "✅ Created user_assignments.md with summary"

# Cleanup temporary files
rm -f app-roles.json

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "✅ Created 6 test users with role assignments"
echo "✅ Created app registrations with roles"
echo "✅ Created managed identities for workload identity"
echo "✅ Generated configuration files"
echo ""
echo "📁 Generated Files:"
echo "  - .env (environment variables)"
echo "  - user_assignments.md (user summary)"
echo ""
echo "🔄 Next Steps:"
echo "  1. Review user_assignments.md for assigned roles"
echo "  2. Configure AKS workload identity with the managed identities"
echo "  3. Deploy and test the applications"
echo "  4. Set up PlainID with user attribute mappings"
echo ""
echo "⚠️  Important Notes:"
echo "  - Update TENANT_DOMAIN, RESOURCE_GROUP, and LOCATION variables at the top of this script"
echo "  - Test users have temporary passwords that must be changed on first login"
echo "  - Review and customize PlainID policies for your specific requirements"
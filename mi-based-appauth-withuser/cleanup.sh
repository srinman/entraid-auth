#!/bin/bash

# Cleanup script for User-Based Authorization Demo
# This script removes all created resources

set -e

echo "🧹 Cleaning up User-Based Authorization Demo"
echo "==========================================="

# Load configuration if available
if [[ -f .env ]]; then
    source .env
    echo "📋 Loaded configuration from .env"
else
    echo "⚠️  No .env file found. Please run setup_user_demo.sh first or manually set variables."
    exit 1
fi

echo "🗑️ This will remove:"
echo "  - App registrations: $API_APP_ID, $CLIENT_APP_ID"
echo "  - Service principals for the apps"
echo "  - User role assignments"
echo "  - Managed identities: workload-identity-api-user, workload-identity-client-user"
echo "  - Test users: testuser1-6@$TENANT_DOMAIN"
echo ""

# Confirm deletion
read -p "Are you sure you want to delete all resources? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled"
    exit 1
fi

echo ""
echo "🔄 Starting cleanup..."

# Function to safely delete resource
safe_delete() {
    local resource_type=$1
    local resource_id=$2
    local description=$3
    
    if [[ -n "$resource_id" ]]; then
        echo "🗑️ Deleting $description..."
        case $resource_type in
            "app")
                az ad app delete --id "$resource_id" 2>/dev/null || echo "⚠️ Failed to delete app $resource_id (may not exist)"
                ;;
            "user")
                az ad user delete --id "$resource_id" 2>/dev/null || echo "⚠️ Failed to delete user $resource_id (may not exist)"
                ;;
            "identity")
                az identity delete --name "$resource_id" --resource-group "$RESOURCE_GROUP" 2>/dev/null || echo "⚠️ Failed to delete identity $resource_id (may not exist)"
                ;;
        esac
    else
        echo "⚠️ Skipping $description - ID not found"
    fi
}

echo ""
echo "📱 Step 1: Removing app registrations..."
echo "========================================"

# Delete app registrations (this also removes service principals and role assignments)
safe_delete "app" "$API_APP_ID" "API app registration"
safe_delete "app" "$CLIENT_APP_ID" "Client app registration"

echo ""
echo "👥 Step 2: Removing test users..."
echo "================================="

# Remove test users
safe_delete "user" "testuser1@$TENANT_DOMAIN" "testuser1"
safe_delete "user" "testuser2@$TENANT_DOMAIN" "testuser2"
safe_delete "user" "testuser3@$TENANT_DOMAIN" "testuser3"
safe_delete "user" "testuser4@$TENANT_DOMAIN" "testuser4"
safe_delete "user" "testuser5@$TENANT_DOMAIN" "testuser5"
safe_delete "user" "testuser6@$TENANT_DOMAIN" "testuser6"

echo ""
echo "🏗️ Step 3: Removing managed identities..."
echo "========================================"

# Remove managed identities
safe_delete "identity" "workload-identity-api-user" "API managed identity"
safe_delete "identity" "workload-identity-client-user" "Client managed identity"

echo ""
echo "📄 Step 4: Cleaning up files..."
echo "==============================="

# Remove generated files
if [[ -f .env ]]; then
    rm .env
    echo "🗑️ Removed .env file"
fi

if [[ -f user_assignments.md ]]; then
    rm user_assignments.md
    echo "🗑️ Removed user_assignments.md file"
fi

echo ""
echo "🎉 Cleanup Complete!"
echo "==================="
echo ""
echo "✅ All resources have been removed:"
echo "  - App registrations and service principals"
echo "  - User role assignments (removed with apps)"
echo "  - Test users"
echo "  - Managed identities"
echo "  - Configuration files"
echo ""
echo "📝 Note: Some resources may have failed to delete if they were already removed"
echo "      or if you don't have sufficient permissions. This is normal."
echo ""
echo "🔄 To set up the demo again, run:"
echo "  ./setup_user_demo.sh"
# Migrating from App Registration to Managed Identity for AKS Workloads (User-Based Authorization)

## Overview

This document provides a comprehensive guide to eliminate app registration dependencies and migrate to managed identity with workload identity for Azure Kubernetes Service (AKS) deployments. **This variant demonstrates user-based authorization** where specific users are assigned different app roles and how this translates to both traditional app registration patterns and modern managed identity + PlainID approaches.

**User Personas for this Demo:**
- **testuser1@company.com** - Plan Administrator (planadmin role)
- **testuser2@company.com** - Account Viewer (accountviewer role)
- **testuser3@company.com** - Account Administrator (accountadmin role)
- **testuser4@company.com** - Account Viewer (accountviewer role)
- **testuser5@company.com** - Account Viewer (accountviewer role)
- **testuser6@company.com** - Account Viewer (accountviewer role)

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Architecture Comparison](#architecture-comparison)
3. [Token Scopes and Authentication Differences](#token-scopes-and-authentication-differences)
4. [Phase 1: App Registration with Workload Identity (Baseline)](#phase-1-app-registration-with-workload-identity-baseline)
5. [Phase 2: Pure Managed Identity Approach](#phase-2-pure-managed-identity-approach)
6. [PlainID Integration](#plainid-integration)
7. [Migration Guide](#migration-guide)
8. [Best Practices](#best-practices)

## Problem Statement

**Current Challenges:**
- Security team approval bottlenecks for app registration changes
- Complex role management in app registrations
- Maintenance overhead for service principals
- Inconsistent authentication patterns across ACA and AKS
- **User role assignments tied to app registration complexity**

**Proposed Solution:**
- Eliminate app registrations where possible
- Use managed identities with workload identity
- Leverage PlainID for fine-grained authorization
- Reduce dependency on Entra ID app registration roles
- **Enable seamless user-based authorization without app registration overhead**

## Architecture Comparison

### Current Architecture (App Registration with User Authorization)
```
User (testuser1) → Sign-In → Client App (AKS) → Workload Identity → App Registration → API App (AKS)
                                                                  ↓
                                            Entra ID User-to-Role Assignments
                                            - testuser1: planadmin
                                            - testuser2: accountviewer
                                            - testuser3: accountadmin
```

### Target Architecture (Managed Identity with PlainID User Authorization)
```
User (testuser1) → Sign-In → Client App (AKS) → Workload Identity → Managed Identity → API App (AKS)
                                                                                       ↓
                                                                   PlainID User Authorization
                                                                   - testuser1: plan_administrator
                                                                   - testuser2: account_viewer
                                                                   - testuser3: account_admin
Client App (AKS) → Workload Identity → Managed Identity → API App (AKS)
                                                        ↓
                                                  PlainID (Fine-grained Authorization)
```

## App Registration Roles Architecture (User-Based Authorization)

### User Role Assignment Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ENTRA ID TENANT                                      │
│                                                                                 │
│  ┌─────────────────────────┐                    ┌─────────────────────────────┐ │
│  │    API APP REGISTRATION │                    │  CLIENT APP REGISTRATION    │ │
│  │                         │                    │                             │ │
│  │  App Roles Defined:     │                    │  No roles defined here      │ │
│  │  ┌─────────────────────┐ │                    │  (only consumes roles)      │ │
│  │  │ planadmin          │ │                    │                             │ │
│  │  │ - id: guid-1       │ │                    │  ┌─────────────────────────┐ │ │
│  │  │ - value: planadmin │ │                    │  │ Service Principal       │ │ │
│  │  │ - displayName: ... │ │                    │  │ (for OAuth flows)       │ │ │
│  │  └─────────────────────┘ │                    │  └─────────────────────────┘ │ │
│  │  ┌─────────────────────┐ │                    │                             │ │
│  │  │ accountviewer      │ │                    └─────────────────────────────┘ │
│  │  │ - id: guid-2       │ │                                                    │
│  │  │ - value: accountvw │ │                                                    │
│  │  └─────────────────────┘ │                                                    │
│  │  ┌─────────────────────┐ │                                                    │
│  │  │ accountadmin       │ │                                                    │
│  │  │ - id: guid-3       │ │                                                    │
│  │  │ - value: accountadm│ │                                                    │
│  │  └─────────────────────┘ │                                                    │
│  │                         │                                                    │
│  │  ┌─────────────────────┐ │                                                    │
│  │  │ Service Principal   │ │                                                    │
│  │  │ (resource owner)    │ │                                                    │
│  │  └─────────────────────┘ │                                                    │
│  └─────────────────────────┘                                                    │
│                                                                                 │
│                        USER ROLE ASSIGNMENTS                                   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                Enterprise Applications - API App                           │ │
│  │                                                                             │ │
│  │  User Assignment 1:                                                        │ │
│  │  ├─ user: testuser1@company.com                                            │ │
│  │  ├─ app-role-id: guid-1 (planadmin)                                        │ │
│  │  └─ resource-id: api-service-principal-id                                  │ │
│  │                                                                             │ │
│  │  User Assignment 2:                                                        │ │
│  │  ├─ user: testuser2@company.com                                            │ │
│  │  ├─ app-role-id: guid-2 (accountviewer)                                    │ │
│  │  └─ resource-id: api-service-principal-id                                  │ │
│  │                                                                             │ │
│  │  User Assignment 3:                                                        │ │
│  │  ├─ user: testuser3@company.com                                            │ │
│  │  ├─ app-role-id: guid-3 (accountadmin)                                     │ │
│  │  └─ resource-id: api-service-principal-id                                  │ │
│  │                                                                             │ │
│  │  User Assignment 4-6:                                                      │ │
│  │  ├─ users: testuser4@company.com, testuser5@company.com, testuser6@company.com │ │
│  │  ├─ app-role-id: guid-2 (accountviewer)                                    │ │
│  │  └─ resource-id: api-service-principal-id                                  │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘

                                    ↓ TOKEN FLOW ↓

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RUNTIME FLOW                                      │
│                                                                                 │
│  ┌─────────────────┐   1. User Signs In     ┌─────────────────────────────────┐  │
│  │      USER       │      to Client App     │        ENTRA ID                │  │
│  │  testuser1@     │  ──────────────────→   │                                │  │
│  │  company.com    │                        │                                │  │
│  │                 │   2. Client requests   │  Access Token contains:        │  │
│  │                 │      token for API     │  {                             │  │
│  │                 │  ──────────────────→   │    "roles": ["planadmin"],    │  │
│  │                 │                        │    "aud": "api://api-app-id", │  │
│  │                 │   3. Access Token      │    "sub": "testuser1-obj-id", │  │
│  │                 │  ←──────────────────   │    "upn": "testuser1@comp...", │  │
│  └─────────────────┘                        │    ...                         │  │
│           │                                 │  }                             │  │
│           │                                 └─────────────────────────────────┘  │
│           │ 4. Client App calls API with User's Token                           │
│           ↓                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                          API APP (AKS Pod)                                 │ │
│  │                                                                             │ │
│  │  4. Token Validation:                                                       │ │
│  │     ├─ Verify signature                                                     │ │
│  │     ├─ Check audience (api://api-app-id)                                   │ │
│  │     ├─ Validate issuer                                                      │ │
│  │     ├─ Extract roles: ["planadmin"]                                        │ │
│  │     └─ Extract user: "testuser1@company.com"                               │ │
│  │                                                                             │ │
│  │  5. User Authorization Check:                                               │ │
│  │     ├─ Endpoint requires "planadmin" role                                  │ │
│  │     ├─ Token contains "planadmin" role for testuser1                      │ │
│  │     ├─ Log: "testuser1 accessing with planadmin role"                     │ │
│  │     └─ Access GRANTED                                                      │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Key Points (User-Based Authorization):

1. **Roles Defined in API App**: All roles (planadmin, accountviewer, accountadmin) are defined in the API app registration manifest

2. **User Role Assignments**: Users are directly assigned to app roles in Enterprise Applications:
   - **testuser1@company.com** → planadmin role
   - **testuser2@company.com** → accountviewer role  
   - **testuser3@company.com** → accountadmin role
   - **testuser4,5,6@company.com** → accountviewer role

3. **User Authentication Flow**: 
   - User signs in to client application
   - Client requests access token for API on behalf of user
   - Token includes user's assigned roles

4. **Token Claims**: Access tokens contain both user identity (upn, sub) and assigned roles in the "roles" claim

5. **API Validation**: API validates token and checks both user identity and role claims for authorization decisions

### User Assignment Commands

```bash
# Get user object IDs
TESTUSER1_ID=$(az ad user show --id "testuser1@company.com" --query "id" -o tsv)
TESTUSER2_ID=$(az ad user show --id "testuser2@company.com" --query "id" -o tsv)
TESTUSER3_ID=$(az ad user show --id "testuser3@company.com" --query "id" -o tsv)
TESTUSER4_ID=$(az ad user show --id "testuser4@company.com" --query "id" -o tsv)
TESTUSER5_ID=$(az ad user show --id "testuser5@company.com" --query "id" -o tsv)
TESTUSER6_ID=$(az ad user show --id "testuser6@company.com" --query "id" -o tsv)

# Get role IDs from API app
PLAN_ADMIN_ROLE_ID=$(az ad app show --id $API_APP_ID --query "appRoles[?value=='planadmin'].id" -o tsv)
ACCOUNT_VIEWER_ROLE_ID=$(az ad app show --id $API_APP_ID --query "appRoles[?value=='accountviewer'].id" -o tsv)
ACCOUNT_ADMIN_ROLE_ID=$(az ad app show --id $API_APP_ID --query "appRoles[?value=='accountadmin'].id" -o tsv)

# Assign users to roles
az ad app-role-assignment create \
  --app-role-id $PLAN_ADMIN_ROLE_ID \
  --principal-id $TESTUSER1_ID \
  --resource-id $API_SP_ID

az ad app-role-assignment create \
  --app-role-id $ACCOUNT_VIEWER_ROLE_ID \
  --principal-id $TESTUSER2_ID \
  --resource-id $API_SP_ID

az ad app-role-assignment create \
  --app-role-id $ACCOUNT_ADMIN_ROLE_ID \
  --principal-id $TESTUSER3_ID \
  --resource-id $API_SP_ID

# Assign multiple users to accountviewer role
for USER_ID in $TESTUSER4_ID $TESTUSER5_ID $TESTUSER6_ID; do
  az ad app-role-assignment create \
    --app-role-id $ACCOUNT_VIEWER_ROLE_ID \
    --principal-id $USER_ID \
    --resource-id $API_SP_ID
done
```

### Microsoft Documentation References for App Role Definition

The following official Microsoft documentation confirms that app roles are defined in the API/resource application registration:

1. **App Roles Definition Location**
   - **URL**: https://learn.microsoft.com/en-us/entra/identity-platform/howto-add-app-roles-in-apps#declare-roles-for-an-application
   - **Key Quote**: *"App roles are defined on an application registration representing a service, app, or API."*

2. **App-Calling-API Scenario**
   - **URL**: https://learn.microsoft.com/en-us/entra/identity-platform/howto-add-app-roles-in-apps#usage-scenario-of-app-roles
   - **Key Quote**: *"If you're implementing app role business logic in an app-calling-API scenario, you have two app registrations. One app registration is for the app, and a second app registration is for the API. In this case, define the app roles and assign them to the user or group in the app registration of the API."*

3. **Protected Web API Verification**
   - **URL**: https://learn.microsoft.com/en-us/entra/identity-platform/scenario-protected-web-api-verification-scope-app-roles
   - **Reference**: Documentation shows API applications validating roles that were defined in their own app registration

These references validate the architecture shown above where:
- **API app registration** defines the roles (planadmin, accountviewer, accountadmin)
- **Client app registration** consumes these roles through assignments
- **Role assignments** link client service principals to API-defined roles

### Phase 2 Architecture: Managed Identity + PlainID (User-Based)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ENTRA ID TENANT                                      │
│                                                                                 │
│  ┌─────────────────────────┐                    ┌─────────────────────────────┐ │
│  │   MANAGED IDENTITY      │                    │   MANAGED IDENTITY          │ │
│  │   (API App)             │                    │   (Client App)              │ │
│  │                         │                    │                             │ │
│  │  ┌─────────────────────┐ │                    │  ┌─────────────────────────┐ │ │
│  │  │ Object ID           │ │                    │  │ Object ID               │ │ │
│  │  │ Client ID           │ │                    │  │ Client ID               │ │ │
│  │  │ Principal ID        │ │                    │  │ Principal ID            │ │ │
│  │  └─────────────────────┘ │                    │  └─────────────────────────┘ │ │
│  │                         │                    │                             │ │
│  │  NO ROLES DEFINED       │                    │  NO ROLES DEFINED           │ │
│  │  (Authorization         │                    │  (Users sign in normally)   │ │
│  │   handled externally)   │                    │                             │ │
│  └─────────────────────────┘                    └─────────────────────────────┘ │
│                                                                                 │
│              USERS STILL AUTHENTICATE WITH ENTRA ID                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │  testuser1@company.com, testuser2@company.com, testuser3@company.com, ...  │ │
│  │  (No role assignments - just normal user authentication)                   │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘

                                    ↓ TOKEN FLOW ↓

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RUNTIME FLOW                                      │
│                                                                                 │
│  ┌─────────────────┐   1. User Signs In    ┌─────────────────────────────────┐  │
│  │      USER       │      & Client gets     │        ENTRA ID                │  │
│  │  testuser1@     │      MI Token for API  │                                │  │
│  │  company.com    │  ──────────────────→   │  MI Token contains:            │  │
│  │                 │                        │  {                             │  │
│  │                 │   2. MI Token          │    "oid": "mi-object-id",     │  │
│  │  Using:         │  ←──────────────────   │    "aud": "management.azure", │  │
│  │  - Managed      │                        │    "idtyp": "MI",             │  │
│  │    Identity     │                        │    ...                         │  │
│  │  - Workload     │                        │  }                             │  │
│  │    Identity     │                        │  + User Context from Sign-In   │  │
│  │                 │                        │    "upn": "testuser1@comp..."  │  │
│  └─────────────────┘                        │  NO ROLES CLAIM                │  │
│           │                                 └─────────────────────────────────┘  │
│           │ 3. API Call with MI Token + User Context                            │
│           ↓                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                          API APP (AKS Pod)                                 │ │
│  │                                                                             │ │
│  │  4. Token Validation:                                                       │ │
│  │     ├─ Verify signature                                                     │ │
│  │     ├─ Check audience (management.azure.com)                               │ │
│  │     ├─ Validate issuer                                                      │ │
│  │     ├─ Verify idtyp = "MI"                                                  │ │
│  │     └─ Extract user context: testuser1@company.com                         │ │
│  │                                                                             │ │
│  │  5. PlainID Authorization:                ┌───────────────────────────────┐ │ │
│  │     ├─ user_id: testuser1@company.com    │         PLAINID               │ │ │
│  │     ├─ resource: "plans"          ────────→                               │ │ │
│  │     ├─ action: "create"                  │  testuser1 Attributes:        │ │ │
│  │     ├─ context: {account_id, time, etc}  │  {                            │ │ │
│  │     │                                    │    "user_id": "testuser1@...",│ │ │
│  │     └─ Decision: PERMIT ←────────────────│    "department": "planning",  │ │ │
│  │        (testuser1 has plan_administrator │    "role": "plan_administrator", │ │
│  │         permissions)                     │    "accounts": [1,2,3,4,5],   │ │ │
│  │                                          │    "permissions": [            │ │ │
│  │                                          │      "plans:create",          │ │ │
│  │                                          │      "plans:read",            │ │ │
│  │                                          │      "plans:update",          │ │ │
│  │                                          │      "plans:delete"           │ │ │
│  │                                          │    ]                          │ │ │
│  │                                          │  }                            │ │ │
│  │                                          │                               │ │ │
│  │                                          │  Policies:                    │ │ │
│  │                                          │  - User-specific rules        │ │ │
│  │                                          │  - Account-based access       │ │ │
│  │                                          │  - Context-aware decisions    │ │ │
│  │                                          └───────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Architecture Comparison Summary (User-Based Authorization)

| Aspect | App Registration (Phase 1) | Managed Identity + PlainID (Phase 2) |
|--------|----------------------------|--------------------------------------|
| **User Management** | Users assigned to app roles in Entra ID | Users managed in PlainID attribute store |
| **Role Definition** | In API app registration | In PlainID policies |
| **User Assignment** | Manual app-role-assignment in Entra ID | Automatic PlainID user attribute lookup |
| **Token Content** | Contains "roles" claim for user | Contains managed identity + user context |
| **Authorization** | Simple role membership check | Fine-grained policy evaluation per user |
| **User Permissions** | Static roles (planadmin, accountviewer) | Dynamic permissions based on user attributes |
| **Context Awareness** | No user context beyond role | Yes (user, time, location, resource-specific) |
| **Security Team Dependency** | High (user role changes require approval) | Low (user attribute changes via PlainID) |
| **Granularity** | Coarse (application-level roles) | Fine (user + resource + action + context) |
| **Audit Trail** | Basic (user role assignments) | Detailed (per-user policy decisions + context) |
| **Scalability** | Limited by Entra ID role model | Flexible user-based policy model |
| **User Experience** | Users need role assignments upfront | Users automatically get appropriate permissions |

## Token Scopes and Authentication Differences

### Understanding Token Scopes

One of the key differences between app registration and managed identity approaches is how tokens are scoped and validated.

#### App Registration Token Scopes (Phase 1)

**Client Token Request:**
```python
# Client requests token for specific app registration
token_scope = "api://12345678-1234-1234-1234-123456789012/.default"
```

**API Token Validation:**
```python
# API validates token against custom audience
payload = jwt.decode(
    token,
    key,
    algorithms=['RS256'],
    audience=f"api://{self.client_id}",  # Custom app registration audience
    issuer=f"https://sts.windows.net/{self.tenant_id}/"
)
```

#### Managed Identity Token Scopes (Phase 2)

**Client Token Request:**
```python
# Client requests token for standard Azure scope
token_scope = "https://management.azure.com/.default"
```

**API Token Validation:**
```python
# API validates token against standard Azure audience
payload = jwt.decode(
    token,
    key,
    algorithms=['RS256'],
    audience="https://management.azure.com/",  # Standard Azure audience
    issuer=f"https://sts.windows.net/{self.tenant_id}/"
)
```

### Why `https://management.azure.com/.default`?

**Managed Identity Standards**: Unlike app registrations which have custom audiences (like `api://your-app-id`), managed identities use well-known Azure scopes. The management scope is the most universal for service-to-service authentication.

**Key Benefits:**
- **Standardized**: No need to configure custom audiences
- **Universal**: Works across all Azure services
- **Simplified**: Reduces configuration complexity
- **Microsoft Recommended**: Follows Azure best practices

### Official Azure Documentation References

1. **Managed Identities Overview**
   - **URL**: https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview
   - **Key Quote**: *"You can use managed identities to authenticate to any resource that supports Microsoft Entra authentication, including your own applications."*

2. **Azure Services Supporting Managed Identities**
   - **URL**: https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/managed-identities-status
   - **Content**: Lists standard scopes used by managed identities for different Azure services

3. **Token Acquisition with Managed Identities**
   - **URL**: https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/how-to-use-vm-token
   - **Examples**: Shows token requests using standard Azure scopes:
     - `https://management.azure.com/` (Azure Resource Manager)
     - `https://vault.azure.net/` (Key Vault)
     - `https://storage.azure.com/` (Storage)

4. **Azure Identity SDK Documentation**
   - **URL**: https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential
   - **Content**: Documents how `DefaultAzureCredential` works with standard Azure scopes

5. **Azure Resource Manager Authentication**
   - **URL**: https://learn.microsoft.com/en-us/rest/api/azure/#authentication
   - **Key Quote**: *"Azure Resource Manager provider (and classic deployment model) APIs use `https://management.core.windows.net/`"* and *"Azure Resource Manager provider APIs use `https://management.azure.com/`"*

### Alternative Azure Scopes for Managed Identity

While `https://management.azure.com/.default` is the most universal, managed identities can also request tokens for other Azure services:

```python
# Key Vault access
vault_scope = "https://vault.azure.net/.default"

# Storage access  
storage_scope = "https://storage.azure.com/.default"

# Graph API access
graph_scope = "https://graph.microsoft.com/.default"
```

**Recommendation**: Use `https://management.azure.com/.default` for custom application authentication as it's the most generic and widely supported scope for managed identity service-to-service authentication.

## Phase 1: App Registration with Workload Identity (User-Based Authorization)

This phase demonstrates the traditional approach using app registrations with workload identity, but with **user-based authorization** where individual users are assigned app roles.

### Prerequisites

1. **AKS Cluster with Workload Identity Enabled**
2. **Azure CLI and kubectl configured**
3. **Python 3.8+ environment**
4. **Test users created in Entra ID**:
   - testuser1@company.com
   - testuser2@company.com
   - testuser3@company.com
   - testuser4@company.com
   - testuser5@company.com
   - testuser6@company.com

### Step 1: Create App Registration

```bash
# Create app registration for API
az ad app create \
  --display-name "api-app-workload-identity" \
  --sign-in-audience "AzureADMyOrg"

# Get the app ID
API_APP_ID=$(az ad app list --display-name "api-app-workload-identity" --query "[0].appId" -o tsv)

# Create app registration for client
az ad app create \
  --display-name "client-app-workload-identity" \
  --sign-in-audience "AzureADMyOrg"

# Get the client app ID
CLIENT_APP_ID=$(az ad app list --display-name "client-app-workload-identity" --query "[0].appId" -o tsv)
```

### Step 2: Define App Roles

Create app roles for the API application:

```bash
# Create app-roles.json
cat > app-roles.json << EOF
[
  {
    "allowedMemberTypes": ["Application"],
    "description": "Plan administrators can manage all planning resources",
    "displayName": "Plan Admin",
    "id": "$(uuidgen)",
    "isEnabled": true,
    "value": "planadmin"
  },
  {
    "allowedMemberTypes": ["Application"],
    "description": "Account viewers can read account information",
    "displayName": "Account Viewer",
    "id": "$(uuidgen)",
    "isEnabled": true,
    "value": "accountviewer"
  },
  {
    "allowedMemberTypes": ["Application"],
    "description": "Account administrators can manage account settings",
    "displayName": "Account Admin",
    "id": "$(uuidgen)",
    "isEnabled": true,
    "value": "accountadmin"
  }
]
EOF

# Update app registration with roles
az ad app update --id $API_APP_ID --app-roles @app-roles.json
```

### Step 3: Create Service Principals and Assign Users to Roles

```bash
# Create service principal for API app
az ad sp create --id $API_APP_ID

# Create service principal for client app (for OAuth flows)
az ad sp create --id $CLIENT_APP_ID

# Get service principal IDs
API_SP_ID=$(az ad sp show --id $API_APP_ID --query "id" -o tsv)
CLIENT_SP_ID=$(az ad sp show --id $CLIENT_APP_ID --query "id" -o tsv)

# Get role IDs from API app
PLAN_ADMIN_ROLE_ID=$(az ad app show --id $API_APP_ID --query "appRoles[?value=='planadmin'].id" -o tsv)
ACCOUNT_VIEWER_ROLE_ID=$(az ad app show --id $API_APP_ID --query "appRoles[?value=='accountviewer'].id" -o tsv)
ACCOUNT_ADMIN_ROLE_ID=$(az ad app show --id $API_APP_ID --query "appRoles[?value=='accountadmin'].id" -o tsv)

# Get user object IDs
TESTUSER1_ID=$(az ad user show --id "testuser1@company.com" --query "id" -o tsv)
TESTUSER2_ID=$(az ad user show --id "testuser2@company.com" --query "id" -o tsv)
TESTUSER3_ID=$(az ad user show --id "testuser3@company.com" --query "id" -o tsv)
TESTUSER4_ID=$(az ad user show --id "testuser4@company.com" --query "id" -o tsv)
TESTUSER5_ID=$(az ad user show --id "testuser5@company.com" --query "id" -o tsv)
TESTUSER6_ID=$(az ad user show --id "testuser6@company.com" --query "id" -o tsv)

# Assign users to specific roles
echo "Assigning testuser1 to planadmin role..."
az ad app-role-assignment create \
  --app-role-id $PLAN_ADMIN_ROLE_ID \
  --principal-id $TESTUSER1_ID \
  --resource-id $API_SP_ID

echo "Assigning testuser2 to accountviewer role..."
az ad app-role-assignment create \
  --app-role-id $ACCOUNT_VIEWER_ROLE_ID \
  --principal-id $TESTUSER2_ID \
  --resource-id $API_SP_ID

echo "Assigning testuser3 to accountadmin role..."
az ad app-role-assignment create \
  --app-role-id $ACCOUNT_ADMIN_ROLE_ID \
  --principal-id $TESTUSER3_ID \
  --resource-id $API_SP_ID

# Assign multiple users to accountviewer role
echo "Assigning testuser4, testuser5, testuser6 to accountviewer role..."
for USER_ID in $TESTUSER4_ID $TESTUSER5_ID $TESTUSER6_ID; do
  az ad app-role-assignment create \
    --app-role-id $ACCOUNT_VIEWER_ROLE_ID \
    --principal-id $USER_ID \
    --resource-id $API_SP_ID
done
```

### Step 4: Setup Workload Identity

```bash
# Create managed identity for AKS workload
az identity create \
  --name "workload-identity-api" \
  --resource-group "your-resource-group" \
  --location "your-location"

az identity create \
  --name "workload-identity-client" \
  --resource-group "your-resource-group" \
  --location "your-location"

# Get identity details
API_IDENTITY_ID=$(az identity show --name "workload-identity-api" --resource-group "your-resource-group" --query "id" -o tsv)
CLIENT_IDENTITY_ID=$(az identity show --name "workload-identity-client" --resource-group "your-resource-group" --query "id" -o tsv)

API_IDENTITY_CLIENT_ID=$(az identity show --name "workload-identity-api" --resource-group "your-resource-group" --query "clientId" -o tsv)
CLIENT_IDENTITY_CLIENT_ID=$(az identity show --name "workload-identity-client" --resource-group "your-resource-group" --query "clientId" -o tsv)

# Create federated credentials
az identity federated-credential create \
  --name "api-federated-credential" \
  --identity-name "workload-identity-api" \
  --resource-group "your-resource-group" \
  --issuer "https://your-aks-cluster-oidc-url" \
  --subject "system:serviceaccount:default:api-service-account" \
  --audience "api://AzureADTokenExchange"

az identity federated-credential create \
  --name "client-federated-credential" \
  --identity-name "workload-identity-client" \
  --resource-group "your-resource-group" \
  --issuer "https://your-aks-cluster-oidc-url" \
  --subject "system:serviceaccount:default:client-service-account" \
  --audience "api://AzureADTokenExchange"
```

### Step 5: Create Kubernetes Service Accounts

```yaml
# api-service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api-service-account
  namespace: default
  annotations:
    azure.workload.identity/client-id: "${API_IDENTITY_CLIENT_ID}"
    azure.workload.identity/tenant-id: "${TENANT_ID}"
---
# client-service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: client-service-account
  namespace: default
  annotations:
    azure.workload.identity/client-id: "${CLIENT_IDENTITY_CLIENT_ID}"
    azure.workload.identity/tenant-id: "${TENANT_ID}"
```

```bash
kubectl apply -f api-service-account.yaml
kubectl apply -f client-service-account.yaml
```

## Python Implementation Examples

### API Application (Flask)

See `api_app_phase1.py` for a complete Flask API implementation with role-based authorization.

### Client Application

See `client_app_phase1.py` for a complete client implementation using workload identity.

### Dependencies

Create a `requirements.txt` file:

```
azure-identity==1.17.1
flask==3.0.3
PyJWT==2.8.0
cryptography==42.0.5
requests==2.32.2
aiohttp==3.9.5
```

### Kubernetes Deployment

```yaml
# api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-app
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-app
  template:
    metadata:
      labels:
        app: api-app
        azure.workload.identity/use: "true"
    spec:
      serviceAccountName: api-service-account
      containers:
      - name: api-app
        image: your-registry/api-app:latest
        ports:
        - containerPort: 8000
        env:
        - name: AZURE_TENANT_ID
          value: "your-tenant-id"
        - name: AZURE_CLIENT_ID
          value: "your-api-app-client-id"
---
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: default
spec:
  selector:
    app: api-app
  ports:
  - port: 8000
    targetPort: 8000
```

```yaml
# client-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: client-app
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: client-app
  template:
    metadata:
      labels:
        app: client-app
        azure.workload.identity/use: "true"
    spec:
      serviceAccountName: client-service-account
      containers:
      - name: client-app
        image: your-registry/client-app:latest
        env:
        - name: AZURE_TENANT_ID
          value: "your-tenant-id"
        - name: AZURE_CLIENT_ID
          value: "your-client-app-client-id"
        - name: API_SCOPE
          value: "api://your-api-app-id/.default"
        - name: API_BASE_URL
          value: "http://api-service:8000"
```

## Phase 2: Pure Managed Identity Approach (User-Based PlainID Authorization)

This phase eliminates app registrations entirely and uses managed identities directly for authentication, with PlainID handling fine-grained **user-based authorization**. Users sign in normally, but authorization decisions are made by PlainID based on user attributes rather than app registration roles.

### Architecture Benefits

**Eliminated Complexity:**
- No app registration management
- No service principal maintenance
- No role assignments in Entra ID
- Reduced security team dependencies
- **No user role assignments in Entra ID**

**Enhanced Security:**
- Managed identity lifecycle tied to Azure resources
- No secrets or certificates to manage
- Automatic token rotation
- Fine-grained authorization via PlainID
- **User-context aware authorization decisions**

**User Experience Benefits:**
- Users sign in once with their normal Entra ID credentials
- Authorization happens transparently via PlainID
- Dynamic permission changes without security team involvement
- Granular, context-aware access control

### Step 1: Create Managed Identities

```bash
# Create user-assigned managed identities
az identity create \
  --name "mi-api-app" \
  --resource-group "your-resource-group" \
  --location "your-location"

az identity create \
  --name "mi-client-app" \
  --resource-group "your-resource-group" \
  --location "your-location"

# Get identity details
API_MI_ID=$(az identity show --name "mi-api-app" --resource-group "your-resource-group" --query "id" -o tsv)
CLIENT_MI_ID=$(az identity show --name "mi-client-app" --resource-group "your-resource-group" --query "id" -o tsv)

API_MI_CLIENT_ID=$(az identity show --name "mi-api-app" --resource-group "your-resource-group" --query "clientId" -o tsv)
CLIENT_MI_CLIENT_ID=$(az identity show --name "mi-client-app" --resource-group "your-resource-group" --query "clientId" -o tsv)

API_MI_PRINCIPAL_ID=$(az identity show --name "mi-api-app" --resource-group "your-resource-group" --query "principalId" -o tsv)
CLIENT_MI_PRINCIPAL_ID=$(az identity show --name "mi-client-app" --resource-group "your-resource-group" --query "principalId" -o tsv)
```

### Step 2: Setup Direct Managed Identity Authentication

```bash
# Create federated credentials for workload identity
az identity federated-credential create \
  --name "api-workload-credential" \
  --identity-name "mi-api-app" \
  --resource-group "your-resource-group" \
  --issuer "https://your-aks-cluster-oidc-url" \
  --subject "system:serviceaccount:default:api-mi-service-account" \
  --audience "api://AzureADTokenExchange"

az identity federated-credential create \
  --name "client-workload-credential" \
  --identity-name "mi-client-app" \
  --resource-group "your-resource-group" \
  --issuer "https://your-aks-cluster-oidc-url" \
  --subject "system:serviceaccount:default:client-mi-service-account" \
  --audience "api://AzureADTokenExchange"
```

### Step 3: Configure Resource Access (Optional)

If you need to access Azure resources, grant appropriate RBAC permissions:

```bash
# Example: Grant access to Key Vault or other Azure services
az role assignment create \
  --assignee $API_MI_PRINCIPAL_ID \
  --role "Key Vault Secrets User" \
  --scope "/subscriptions/your-subscription/resourceGroups/your-resource-group/providers/Microsoft.KeyVault/vaults/your-keyvault"
```

### Step 4: Update Kubernetes Service Accounts

```yaml
# api-mi-service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api-mi-service-account
  namespace: default
  annotations:
    azure.workload.identity/client-id: "${API_MI_CLIENT_ID}"
    azure.workload.identity/tenant-id: "${TENANT_ID}"
---
# client-mi-service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: client-mi-service-account
  namespace: default
  annotations:
    azure.workload.identity/client-id: "${CLIENT_MI_CLIENT_ID}"
    azure.workload.identity/tenant-id: "${TENANT_ID}"
```

### Phase 2 Python Implementation

See `api_app_phase2.py` and `client_app_phase2.py` for complete implementations using managed identity with PlainID integration.

### Phase 2 Kubernetes Deployment

```yaml
# api-mi-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-app-mi
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-app-mi
  template:
    metadata:
      labels:
        app: api-app-mi
        azure.workload.identity/use: "true"
    spec:
      serviceAccountName: api-mi-service-account
      containers:
      - name: api-app
        image: your-registry/api-app-mi:latest
        ports:
        - containerPort: 8000
        env:
        - name: AZURE_TENANT_ID
          value: "your-tenant-id"
        - name: AZURE_CLIENT_ID
          value: "your-api-mi-client-id"
        - name: PLAINID_ENDPOINT
          value: "https://your-plainid-instance.com/api/v1"
        - name: PLAINID_TOKEN
          valueFrom:
            secretKeyRef:
              name: plainid-secret
              key: token
---
apiVersion: v1
kind: Service
metadata:
  name: api-service-mi
  namespace: default
spec:
  selector:
    app: api-app-mi
  ports:
  - port: 8000
    targetPort: 8000
```

```yaml
# client-mi-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: client-app-mi
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: client-app-mi
  template:
    metadata:
      labels:
        app: client-app-mi
        azure.workload.identity/use: "true"
    spec:
      serviceAccountName: client-mi-service-account
      containers:
      - name: client-app
        image: your-registry/client-app-mi:latest
        env:
        - name: AZURE_TENANT_ID
          value: "your-tenant-id"
        - name: AZURE_CLIENT_ID
          value: "your-client-mi-client-id"
        - name: API_BASE_URL
          value: "http://api-service-mi:8000"
```

## PlainID Integration (User-Based Authorization)

### Why PlainID Eliminates App Registration User Role Assignments

**Traditional Approach Problems:**
- Coarse-grained roles in Entra ID app registrations
- Security team bottlenecks for user role changes
- Limited context-aware authorization
- Tight coupling between authentication and authorization
- **Manual user role assignments in Enterprise Applications**

**PlainID Benefits:**
- **Fine-grained permissions**: Resource and action-level control
- **Dynamic authorization**: Context-aware decisions based on user attributes
- **Policy as code**: Version-controlled authorization policies
- **Audit and compliance**: Detailed authorization logs and decisions
- **User-centric authorization**: Direct user identity to permission mapping
- **No Entra ID role assignments**: Users managed in PlainID attribute store

### User Attribute Mapping

In Phase 2, PlainID maps users directly without app registration roles:

```json
{
  "user_mappings": {
    "testuser1@company.com": {
      "user_id": "testuser1@company.com",
      "department": "planning",
      "role": "plan_administrator",
      "permissions": ["plans:create", "plans:update", "plans:delete", "plans:read"],
      "assigned_accounts": [1, 2, 3, 4, 5],
      "clearance_level": "admin"
    },
    "testuser2@company.com": {
      "user_id": "testuser2@company.com", 
      "department": "finance",
      "role": "account_viewer",
      "permissions": ["accounts:read"],
      "assigned_accounts": [1, 2],
      "clearance_level": "standard"
    },
    "testuser3@company.com": {
      "user_id": "testuser3@company.com",
      "department": "operations", 
      "role": "account_administrator",
      "permissions": ["accounts:read", "accounts:update", "accounts:delete"],
      "assigned_accounts": [3, 4, 5],
      "clearance_level": "admin"
    },
    "testuser4@company.com": {
      "user_id": "testuser4@company.com",
      "department": "sales",
      "role": "account_viewer", 
      "permissions": ["accounts:read"],
      "assigned_accounts": [1],
      "clearance_level": "standard"
    },
    "testuser5@company.com": {
      "user_id": "testuser5@company.com",
      "department": "marketing",
      "role": "account_viewer",
      "permissions": ["accounts:read"],
      "assigned_accounts": [2, 3],
      "clearance_level": "standard"
    },
    "testuser6@company.com": {
      "user_id": "testuser6@company.com",
      "department": "support",
      "role": "account_viewer",
      "permissions": ["accounts:read"],
      "assigned_accounts": [1, 2, 3],
      "clearance_level": "standard"
    }
  }
}
```

### PlainID Policy Examples (User-Based)

Here are example policies that replace app registration role assignments:

```json
{
  "policies": [
    {
      "name": "testuser1_plan_admin_policy",
      "description": "Allow testuser1 full plan administration access",
      "rule": {
        "condition": "AND",
        "rules": [
          {
            "attribute": "user.user_id",
            "operator": "EQUALS", 
            "value": "testuser1@company.com"
          },
          {
            "attribute": "resource.type",
            "operator": "EQUALS",
            "value": "plans"
          },
          {
            "attribute": "action",
            "operator": "IN",
            "value": ["create", "read", "update", "delete"]
          }
        ]
      },
      "effect": "PERMIT"
    },
    {
      "name": "account_viewer_users_policy",
      "description": "Allow testuser2,4,5,6 to view accounts they're assigned to",
      "rule": {
        "condition": "AND", 
        "rules": [
          {
            "attribute": "user.user_id",
            "operator": "IN",
            "value": ["testuser2@company.com", "testuser4@company.com", "testuser5@company.com", "testuser6@company.com"]
          },
          {
            "attribute": "resource.type",
            "operator": "EQUALS",
            "value": "accounts"
          },
          {
            "attribute": "action",
            "operator": "EQUALS",
            "value": "read"
          },
          {
            "attribute": "context.account_id",
            "operator": "IN", 
            "value": "user.assigned_accounts"
          }
        ]
      },
      "effect": "PERMIT"
    },
    {
      "name": "testuser3_account_admin_policy",
      "description": "Allow testuser3 account administration for assigned accounts",
      "rule": {
        "condition": "AND",
        "rules": [
          {
            "attribute": "user.user_id",
            "operator": "EQUALS",
            "value": "testuser3@company.com"
          },
          {
            "attribute": "resource.type", 
            "operator": "EQUALS",
            "value": "accounts"
          },
          {
            "attribute": "action",
            "operator": "IN",
            "value": ["read", "update", "delete"]
          },
          {
            "attribute": "context.account_id",
            "operator": "IN",
            "value": "user.assigned_accounts"
          }
        ]
      },
      "effect": "PERMIT"
    },
    {
      "name": "plan_read_policy",
      "description": "Allow reading plans for authorized users",
      "rule": {
        "condition": "AND",
        "rules": [
          {
            "attribute": "user.department",
            "operator": "IN",
            "value": ["planning", "management", "finance"]
          },
          {
            "attribute": "resource.type",
            "operator": "EQUALS",
            "value": "plans"
          },
          {
            "attribute": "action",
            "operator": "EQUALS", 
            "value": "read"
          }
        ]
      },
      "effect": "PERMIT"
    },
    {
      "name": "plan_create_policy", 
      "description": "Allow creating plans for plan administrators",
      "rule": {
        "condition": "AND",
        "rules": [
          {
            "attribute": "user.role",
            "operator": "EQUALS",
            "value": "plan_administrator"
          },
          {
            "attribute": "resource.type",
            "operator": "EQUALS",
            "value": "plans"
          },
          {
            "attribute": "action",
            "operator": "EQUALS",
            "value": "create"
          }
        ]
      },
      "effect": "PERMIT"
    },
    {
      "name": "account_context_policy",
      "description": "Allow account access based on user's assigned accounts",
      "rule": {
        "condition": "AND",
        "rules": [
          {
            "attribute": "context.account_id",
            "operator": "IN",
            "value": "user.assigned_accounts"
          },
          {
            "attribute": "resource.type",
            "operator": "EQUALS",
            "value": "accounts"
          },
          {
            "condition": "OR",
            "rules": [
              {
                "attribute": "action",
                "operator": "EQUALS",
                "value": "read"
              },
              {
                "condition": "AND",
                "rules": [
                  {
                    "attribute": "action",
                    "operator": "EQUALS",
                    "value": "update"
                  },
                  {
                    "attribute": "user.role",
                    "operator": "IN",
                    "value": ["account_admin", "super_admin"]
                  }
                ]
              }
            ]
          }
        ]
      },
      "effect": "PERMIT"
    }
  ]
}
```

### User Attribute Management

With PlainID, user attributes can be sourced from multiple systems:

```json
{
  "user_attributes": {
    "managed_identity_id": "12345678-1234-1234-1234-123456789012",
    "department": "planning",
    "role": "plan_administrator", 
    "assigned_accounts": [1, 2, 5],
    "clearance_level": "confidential",
    "location": "us-east",
    "cost_center": "CC-1001"
  }
}
```

### Context-Aware Authorization

PlainID enables dynamic decisions based on request context:

```python
# Example context sent to PlainID
context = {
    'client_id': managed_identity_client_id,
    'tenant_id': tenant_id,
    'request_path': '/api/accounts/123/settings',
    'request_method': 'PUT',
    'account_id': 123,
    'client_ip': '10.0.1.100',
    'time_of_day': '14:30',
    'day_of_week': 'Tuesday'
}
```

## Migration Guide

### Pre-Migration Checklist

1. **Audit Current App Registration Usage**
   ```bash
   # List current app registrations
   az ad app list --query "[].{displayName:displayName, appId:appId, createdDateTime:createdDateTime}"
   
   # List role assignments
   az ad app show --id $APP_ID --query "appRoles[].{displayName:displayName, value:value}"
   ```

2. **Document Current Role Mappings**
   Create a mapping document:
   ```
   App Registration Role -> PlainID Permission
   - planadmin -> plans:create, plans:update, plans:delete, plans:read
   - accountviewer -> accounts:read
   - accountadmin -> accounts:read, accounts:update, accounts:delete
   ```

3. **Setup PlainID Environment**
   - Configure PlainID policies
   - Import user attributes
   - Test authorization decisions

### Step-by-Step Migration

#### Step 1: Parallel Setup (Zero Downtime)

1. **Create Managed Identities** (as shown in Phase 2)
2. **Deploy Phase 2 Applications** alongside existing apps
3. **Configure PlainID** with equivalent policies

#### Step 2: Gradual Traffic Migration

```yaml
# Use canary deployment to gradually shift traffic
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: api-migration-rollout
spec:
  replicas: 4
  strategy:
    canary:
      steps:
      - setWeight: 25  # 25% to new managed identity version
      - pause: {duration: 10m}
      - setWeight: 50  # 50% to new version
      - pause: {duration: 10m} 
      - setWeight: 75  # 75% to new version
      - pause: {duration: 10m}
      - setWeight: 100 # 100% to new version
  selector:
    matchLabels:
      app: api-service
  template:
    metadata:
      labels:
        app: api-service
    spec:
      # New managed identity configuration
```

#### Step 3: Validation and Testing

```bash
# Test script to validate both approaches
#!/bin/bash

echo "Testing Phase 1 (App Registration)..."
kubectl run test-client-phase1 --image=your-registry/client-app-phase1:latest --env="API_BASE_URL=http://api-service:8000" --restart=Never

echo "Testing Phase 2 (Managed Identity)..."
kubectl run test-client-phase2 --image=your-registry/client-app-phase2:latest --env="API_BASE_URL=http://api-service-mi:8000" --restart=Never

# Compare outputs
kubectl logs test-client-phase1
kubectl logs test-client-phase2
```

#### Step 4: Complete Migration

1. **Update DNS/Load Balancer** to point to new services
2. **Monitor PlainID authorization logs** for any issues
3. **Scale down Phase 1 applications**
4. **Clean up app registrations** (after verification period)

```bash
# Cleanup script (run after successful migration)
#!/bin/bash

# Remove app registration role assignments
az ad app-role-assignment delete --app-role-assignment-id $ASSIGNMENT_ID

# Delete app registrations (optional - keep for rollback initially)
# az ad app delete --id $APP_ID
```

## Best Practices

### Security

1. **Token Caching**: Cache managed identity tokens (24-hour validity)
2. **Fail Secure**: Deny access if PlainID is unavailable
3. **Audit Logging**: Log all authorization decisions
4. **Regular Reviews**: Periodically review PlainID policies

### Performance

1. **Connection Pooling**: Use persistent connections to PlainID
2. **Async Operations**: Use async HTTP clients for better performance
3. **Caching**: Cache authorization decisions for short periods
4. **Circuit Breaker**: Implement circuit breaker pattern for PlainID calls

### Monitoring

```yaml
# Example monitoring configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: monitoring-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'api-app-mi'
      static_configs:
      - targets: ['api-service-mi:8000']
      metrics_path: '/metrics'
    - job_name: 'plainid'
      static_configs:
      - targets: ['plainid-service:9090']
```

### Key Metrics to Monitor

- **Authentication Success Rate**: Managed identity token acquisition
- **Authorization Decision Time**: PlainID response latency
- **Authorization Success Rate**: Permit vs Deny decisions
- **Error Rates**: Token validation and PlainID communication errors

## Conclusion

**Phase 1 (App Registration)** demonstrates the traditional approach with its inherent complexities around security team dependencies and coarse-grained role management.

**Phase 2 (Managed Identity + PlainID)** eliminates these bottlenecks by:
- Removing app registration dependencies
- Enabling fine-grained, context-aware authorization
- Reducing security team overhead
- Providing better audit and compliance capabilities

The migration approach ensures zero downtime while providing a clear path forward for teams wanting to modernize their authentication and authorization architecture on Azure.

### Research Validation

Based on Microsoft documentation and PlainID capabilities:

✅ **Managed identities can authenticate to any Entra ID-protected resource**  
✅ **PlainID provides fine-grained authorization beyond Entra ID app roles**  
✅ **Workload identity supports both app registrations and managed identities**  
✅ **External authorization systems like PlainID eliminate need for app registration roles**  

This approach aligns with Microsoft's recommendation for service-to-service authentication within Azure and modern zero-trust authorization patterns.

## Appendix: Microsoft App Role Patterns

This appendix provides detailed architecture diagrams for the two primary app role patterns documented by Microsoft, illustrating where roles are defined and how they flow through tokens.

### Pattern 1: User Sign-In Application Scenario

**Microsoft Documentation Quote**: *"If you're implementing app role business logic that signs in the users in your application scenario, first define the app roles in App registrations. Then, an admin assigns them to users and groups in the Enterprise applications pane. Depending on the scenario, these assigned app roles are included in different tokens that are issued for your application. For example, for an app that signs in users, the roles claims are included in the ID token. When your application calls an API, the roles claims are included in the access token."*

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     PATTERN 1: USER SIGN-IN SCENARIO                           │
│                                                                                 │
│  ┌─────────────────────────┐                    ┌─────────────────────────────┐ │
│  │   APPLICATION REGISTRATION │                    │   EXTERNAL API REGISTRATION │ │
│  │                         │                    │                             │ │
│  │  App Roles Defined:     │                    │  May have its own roles     │ │
│  │  ┌─────────────────────┐ │                    │  (separate from app roles)  │ │
│  │  │ manager            │ │                    │                             │ │
│  │  │ employee           │ │                    │  ┌─────────────────────────┐ │ │
│  │  │ admin              │ │                    │  │ read, write, delete     │ │ │
│  │  └─────────────────────┘ │                    │  └─────────────────────────┘ │ │
│  │                         │                    │                             │ │
│  │  ┌─────────────────────┐ │                    └─────────────────────────────┘ │
│  │  │ Service Principal   │ │                                                  │
│  │  │                     │ │                                                  │
│  │  └─────────────────────┘ │                                                  │
│  └─────────────────────────┘                                                  │
│                                                                                 │
│                     USER & GROUP ASSIGNMENTS                                   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                  Enterprise Applications                                   │ │
│  │                                                                             │ │
│  │  User Assignment 1:                                                        │ │
│  │  ├─ user: john@company.com                                                 │ │
│  │  └─ role: manager                                                          │ │
│  │                                                                             │ │
│  │  User Assignment 2:                                                        │ │
│  │  ├─ user: jane@company.com                                                 │ │
│  │  └─ role: employee                                                         │ │
│  │                                                                             │ │
│  │  Group Assignment:                                                          │ │
│  │  ├─ group: IT-Admins                                                       │ │
│  │  └─ role: admin                                                            │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘

                                    ↓ TOKEN FLOW ↓

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RUNTIME FLOW                                      │
│                                                                                 │
│  ┌─────────────────┐   1. User Sign-In     ┌─────────────────────────────────┐  │
│  │      USER       │  ──────────────────→   │        ENTRA ID                │  │
│  │  john@company   │                        │                                │  │
│  │     .com        │   2. ID Token          │  ID Token contains:            │  │
│  │                 │  ←──────────────────   │  {                             │  │
│  └─────────────────┘                        │    "roles": ["manager"],      │  │
│           │                                 │    "aud": "app-client-id",    │  │
│           │                                 │    "sub": "user-object-id",   │  │
│           │                                 │    ...                         │  │
│           │                                 │  }                             │  │
│           │                                 └─────────────────────────────────┘  │
│           │ 3. Access Application                                               │
│           ↓                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                       APPLICATION                                          │ │
│  │                                                                             │ │
│  │  4. ID Token Validation:                                                    │ │
│  │     ├─ Verify signature                                                     │ │
│  │     ├─ Check audience (app-client-id)                                      │ │
│  │     ├─ Validate issuer                                                      │ │
│  │     └─ Extract roles: ["manager"]                                          │ │
│  │                                                                             │ │
│  │  5. When calling External API:                                             │ │
│  │     ├─ Request access token for API                                        │ │
│  │     ├─ Access token includes user roles                                    │ │
│  │     └─ Pass token to API                                                   │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Pattern 2: App-Calling-API Scenario

**Microsoft Documentation Quote**: *"If you're implementing app role business logic in an app-calling-API scenario, you have two app registrations. One app registration is for the app, and a second app registration is for the API. In this case, define the app roles and assign them to the user or group in the app registration of the API. When the user authenticates with the app and requests an access token to call the API, a roles claim is included in the token."*

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    PATTERN 2: APP-CALLING-API SCENARIO                         │
│                                                                                 │
│  ┌─────────────────────────┐                    ┌─────────────────────────────┐ │
│  │   CLIENT APP REGISTRATION │                    │    API APP REGISTRATION     │ │
│  │                         │                    │                             │ │
│  │  NO ROLES DEFINED       │                    │  App Roles Defined:         │ │
│  │  (Consumes API roles)   │                    │  ┌─────────────────────────┐ │ │
│  │                         │                    │  │ data.read              │ │ │
│  │  ┌─────────────────────┐ │                    │  │ data.write             │ │ │
│  │  │ Service Principal   │ │                    │  │ data.delete            │ │ │
│  │  │ (for role assign.)  │ │                    │  │ admin.manage           │ │ │
│  │  └─────────────────────┘ │                    │  └─────────────────────────┘ │ │
│  │                         │                    │                             │ │
│  └─────────────────────────┘                    │  ┌─────────────────────────┐ │ │
│                                                 │  │ Service Principal       │ │ │
│                                                 │  │ (resource owner)        │ │ │
│                                                 │  └─────────────────────────┘ │ │
│                                                 └─────────────────────────────┘ │
│                                                                                 │
│                            ROLE ASSIGNMENTS                                     │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                Enterprise Applications - API App                           │ │
│  │                                                                             │ │
│  │  User Assignment 1:                                                        │ │
│  │  ├─ user: john@company.com                                                 │ │
│  │  └─ role: data.read                                                        │ │
│  │                                                                             │ │
│  │  User Assignment 2:                                                        │ │
│  │  ├─ user: jane@company.com                                                 │ │
│  │  └─ role: data.write                                                       │ │
│  │                                                                             │ │
│  │  App Assignment:                                                            │ │
│  │  ├─ app: client-app-service-principal                                      │ │
│  │  └─ role: data.read                                                        │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘

                                    ↓ TOKEN FLOW ↓

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RUNTIME FLOW                                      │
│                                                                                 │
│  ┌─────────────────┐   1. User Auth with    ┌─────────────────────────────────┐  │
│  │      USER       │      Client App         │        ENTRA ID                │  │
│  │  john@company   │  ──────────────────→    │                                │  │
│  │     .com        │                         │                                │  │
│  │                 │   2. Request Access     │                                │  │
│  │                 │      Token for API      │  Access Token contains:        │  │
│  │                 │  ──────────────────→    │  {                             │  │
│  │                 │                         │    "roles": ["data.read"],    │  │
│  │                 │   3. Access Token       │    "aud": "api://api-app-id", │  │
│  │                 │  ←──────────────────    │    "sub": "user-object-id",   │  │
│  └─────────────────┘                         │    ...                         │  │
│           │                                  │  }                             │  │
│           │                                  └─────────────────────────────────┘  │
│           │ 4. Use Client App to call API                                       │
│           ↓                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                       CLIENT APP                                           │ │
│  │                                                                             │ │
│  │  5. Call API with Access Token:                                            │ │
│  │     ├─ Include token in Authorization header                               │ │
│  │     ├─ Token contains user's API roles                                     │ │
│  │     └─ Send request to API                                                 │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│           │ 6. API Call with Token                                              │
│           ↓                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                          API APP                                           │ │
│  │                                                                             │ │
│  │  7. Token Validation:                                                       │ │
│  │     ├─ Verify signature                                                     │ │
│  │     ├─ Check audience (api://api-app-id)                                   │ │
│  │     ├─ Validate issuer                                                      │ │
│  │     └─ Extract roles: ["data.read"]                                        │ │
│  │                                                                             │ │
│  │  8. Authorization Check:                                                    │ │
│  │     ├─ Endpoint requires "data.read" role                                  │ │
│  │     ├─ Token contains "data.read" role                                     │ │
│  │     └─ Access GRANTED                                                      │ │
│  │                                                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Key Differences Between Patterns

| Aspect | Pattern 1: User Sign-In | Pattern 2: App-Calling-API |
|--------|------------------------|----------------------------|
| **Role Definition** | In the application registration | In the API registration |
| **User Assignment** | Users assigned to app roles | Users assigned to API roles |
| **Token Type** | ID Token (sign-in) + Access Token (API calls) | Access Token for API |
| **Role Location** | Both ID and Access tokens | Access token only |
| **Audience** | App client ID (ID token) + API audience (Access token) | API audience |
| **Authorization Point** | Application + API | API only |
| **Use Case** | Web apps with integrated authorization | Client apps calling protected APIs |

### Documentation References

Both patterns are documented in Microsoft's official documentation:

- **Pattern 1 & 2 Source**: https://learn.microsoft.com/en-us/entra/identity-platform/howto-add-app-roles-in-apps#usage-scenario-of-app-roles
- **Protected API Verification**: https://learn.microsoft.com/en-us/entra/identity-platform/scenario-protected-web-api-verification-scope-app-roles

The documentation in this guide primarily focuses on **Pattern 2** (App-Calling-API scenario) which is the most common pattern for microservices and API-based architectures in AKS environments.

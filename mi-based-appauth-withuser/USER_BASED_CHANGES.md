# User-Based Authorization Changes

This directory (`mi-based-appauth-withuser`) contains a modified version of the original migration guide that demonstrates **user-based authorization** instead of service principal authorization.

## Key Differences from Original

### User Personas
- **testuser1@company.com** - Plan Administrator (planadmin role)
- **testuser2@company.com** - Account Viewer (accountviewer role)
- **testuser3@company.com** - Account Administrator (accountadmin role)
- **testuser4@company.com** - Account Viewer (accountviewer role)
- **testuser5@company.com** - Account Viewer (accountviewer role)
- **testuser6@company.com** - Account Viewer (accountviewer role)

### Phase 1 Changes (App Registration with User Authorization)

#### Original Phase 1:
- Service principals assigned to app roles
- Client app service principal gets role assignments
- Tokens contain roles based on service principal assignments

#### User-Based Phase 1:
- **Individual users** assigned to app roles in Enterprise Applications
- Users sign in to client application
- Client requests access tokens **on behalf of users**
- Tokens contain both user identity AND assigned roles
- API validates both user context and role claims

#### Key Implementation Changes:
```bash
# Original: Assign service principal to role
az ad app-role-assignment create \
  --app-role-id $PLAN_ADMIN_ROLE_ID \
  --principal-id $CLIENT_SP_ID \
  --resource-id $API_SP_ID

# User-Based: Assign individual users to roles
az ad app-role-assignment create \
  --app-role-id $PLAN_ADMIN_ROLE_ID \
  --principal-id $TESTUSER1_ID \
  --resource-id $API_SP_ID
```

### Phase 2 Changes (Managed Identity with User-Based PlainID)

#### Original Phase 2:
- Managed identity authentication
- PlainID authorization based on managed identity object ID
- Generic user attributes in PlainID

#### User-Based Phase 2:
- **Users still sign in** with their Entra ID credentials
- Client app uses managed identity for service-to-service authentication
- **User context preserved** and passed to PlainID
- PlainID policies based on **specific user identities**
- User attributes mapped per individual user in PlainID

#### Key Implementation Changes:
```python
# Original: PlainID call with MI object ID
context = {
    'client_id': managed_identity_client_id,
    'resource': 'plans',
    'action': 'create'
}

# User-Based: PlainID call with user context
context = {
    'user_id': 'testuser1@company.com',  # Actual user
    'client_id': managed_identity_client_id,
    'resource': 'plans', 
    'action': 'create'
}
```

## Architecture Flow Comparison

### Phase 1 User Flow:
```
User (testuser1) → Sign-In → Client App → Request Token for API → 
Access Token (with user roles) → API validates user + roles
```

### Phase 2 User Flow:
```
User (testuser1) → Sign-In → Client App → MI Token + User Context → 
API → PlainID (user-specific authorization) → Decision
```

## Benefits of User-Based Approach

### Phase 1 Benefits:
- **User accountability**: Clear audit trail of which user performed actions
- **Granular assignment**: Different users can have different role combinations
- **User-specific tokens**: Tokens contain actual user identity for logging/compliance

### Phase 2 Benefits:
- **No Entra ID role management**: Users managed entirely in PlainID
- **User-specific policies**: Granular policies per user or user groups
- **Dynamic permissions**: User permissions can change without Entra ID updates
- **Rich user context**: PlainID can consider user department, location, time, etc.

## Migration Considerations

1. **User Management**: Must create test users in Entra ID before setup
2. **Token Flow**: Client apps must handle user authentication flows
3. **API Updates**: APIs must extract and validate user context
4. **PlainID Setup**: Must configure user-specific attribute mappings
5. **Audit Requirements**: Enhanced logging for user-specific actions

## Use Cases

This user-based approach is ideal for:
- **Multi-user applications** where different users need different permissions
- **Compliance requirements** that need user-level audit trails
- **Dynamic authorization** based on user attributes (department, role, location)
- **Granular access control** where permissions vary by user and context
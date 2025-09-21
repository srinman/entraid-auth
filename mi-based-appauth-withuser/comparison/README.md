# Migration Comparison Script

This script compares the authentication and authorization approaches between Phase 1 (App Registration) and Phase 2 (Managed Identity + PlainID).

## Usage

```bash
# Set environment variables
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID_PHASE1="app-registration-client-id"
export AZURE_CLIENT_ID_PHASE2="managed-identity-client-id"
export API_SCOPE_PHASE1="api://app-registration-id/.default"
export PLAINID_ENDPOINT="https://your-plainid-instance.com/api/v1"
export PLAINID_TOKEN="your-plainid-token"

# Run comparison
python comparison.py
```

## Key Differences Demonstrated

### Authentication
- **Phase 1**: App registration with federated credentials
- **Phase 2**: Direct managed identity authentication

### Authorization  
- **Phase 1**: Entra ID app registration roles (coarse-grained)
- **Phase 2**: PlainID policies (fine-grained, context-aware)

### Token Validation
- **Phase 1**: Validates against app registration audience
- **Phase 2**: Validates against Azure management audience

### Permission Checking
- **Phase 1**: Simple role membership check
- **Phase 2**: Dynamic policy evaluation with context

## Expected Outcomes

The comparison should show:
1. Similar authentication success rates
2. More granular authorization decisions in Phase 2
3. Reduced dependency on security team for role changes
4. Better audit trail and context awareness in Phase 2
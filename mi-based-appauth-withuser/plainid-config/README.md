# PlainID Configuration Examples

This directory contains example configurations for integrating PlainID with the managed identity approach.

## Policy Configuration

The `policies.json` file contains example PlainID policies that replace Entra ID app registration roles.

## User Attributes

The `user-attributes.json` file shows how to structure user attributes in PlainID.

## Integration Patterns

### 1. Synchronous Authorization
```python
# Direct API call to PlainID for each authorization check
result = plainid_client.authorize(user_id, resource, action, context)
```

### 2. Cached Authorization  
```python
# Cache authorization decisions for performance
@cache(ttl=300)  # 5 minute cache
def check_permission(user_id, resource, action):
    return plainid_client.authorize(user_id, resource, action)
```

### 3. Batch Authorization
```python
# Check multiple permissions in one call
permissions = plainid_client.batch_authorize([
    (user_id, "plans", "read"),
    (user_id, "accounts", "read"),
    (user_id, "accounts/123", "update")
])
```

## Migration from App Registration Roles

| App Registration Role | PlainID Resource | PlainID Action | Additional Context |
|----------------------|------------------|----------------|-------------------|
| `planadmin` | `plans` | `create`, `read`, `update`, `delete` | department, cost_center |
| `accountviewer` | `accounts` | `read` | assigned_accounts |
| `accountadmin` | `accounts` | `read`, `update`, `delete` | assigned_accounts, role |

## Environment Variables for PlainID

```bash
# PlainID Configuration
PLAINID_ENDPOINT=https://your-plainid-instance.com/api/v1
PLAINID_TOKEN=your-plainid-api-token
PLAINID_TIMEOUT=5  # seconds
PLAINID_CACHE_TTL=300  # seconds

# Fallback behavior when PlainID is unavailable
PLAINID_FAIL_OPEN=false  # Set to true only in dev environments
```
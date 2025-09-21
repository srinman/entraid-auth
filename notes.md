

https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview#what-are-managed-identities


**You can use managed identities to authenticate to any resource that supports Microsoft Entra authentication, including your own applications.** 


Two Options:  

1)Use MI directly   
2)Use MI as FIC  

https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview#use-managed-identity-as-a-federated-identity-credential-fic-on-an-entra-id-app   


Federated Identity Credential:  Use Managed identity as FIC on an Entra App (limit of 20 FIC on an EntraID app)
Workload Identity Federation 

AKS enables this with Workload identity which can be tied to App Registration or Managed Identity   
ACA enables this with Managed identity (no App registration support)



https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/secretless-authentication#accesses-microsoft-entra-protected-resources-same-tenant   

**For scenarios where you need service-to-service authentication between Azure resources and the resources are in the same tenant, managed identities and the DefaultAzureCredential class in the Azure Identity client library are the recommended option.**  


AKS and K8S are considered 'External Workload'    
https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/secretless-authentication#external-workload-outside-azure-accesses-microsoft-entra-protected-resources   


https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview-for-developers?tabs=python#cache-the-tokens-you-acquire  
**For performance and reliability, we recommend that your application caches tokens in local memory, or encrypted if you want to save them to disk. As Managed identity tokens are valid for 24 hours, there's no benefit in requesting new tokens regularly, as a cached one will be returned from the token issuing endpoint. If you exceed the request limits, you'll be rate limited and receive an HTTP 429 error.**
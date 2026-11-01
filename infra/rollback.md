# Rollback — Proyecto Río Claro

## Status: No rollback performed

The public Web App is running. Roll back only if explicitly approved and after
confirming the active subscription and exact resource names. The resource
group `rg-rio-claro-ai901` is pre-existing and must never be deleted.

Deployment status and the user's reported sign-out/re-authentication behavior
are tracked in `deployment.md`. Separate `obrero` and `finanzas` role tests were omitted by
the user's decision; they are neither reported as verified nor treated as
rollback blockers.

The following resources were created for this deployment:

- Web App `azapplh7c7u3mxydas`
- Linux App Service Plan `azasplh7c7u3mxydas`
- User-assigned managed identity `azidnlh7c7u3mxydas`
- Diagnostic setting `azdglh7c7u3mxydas` on the Web App

With the correct subscription selected, remove only those resources:

```powershell
$subscription = '<Azure for Students subscription ID>'
$resourceGroup = 'rg-rio-claro-ai901'
$webApp = 'azapplh7c7u3mxydas'

az monitor diagnostic-settings delete `
  --name 'azdglh7c7u3mxydas' `
  --resource "/subscriptions/$subscription/resourceGroups/$resourceGroup/providers/Microsoft.Web/sites/$webApp"
az webapp delete --name $webApp --resource-group $resourceGroup --subscription $subscription
az appservice plan delete --name 'azasplh7c7u3mxydas' --resource-group $resourceGroup --subscription $subscription --yes
az identity delete --name 'azidnlh7c7u3mxydas' --resource-group $resourceGroup --subscription $subscription
```

The diagnostic setting is removed before its Web App. Do not delete the
resource group, existing Foundry, Application Insights, Log Analytics, or any
other pre-existing resource.

The deployed callback
`https://azapplh7c7u3mxydas.azurewebsites.net/oauth2callback` was added to an
existing Entra application registration. If rolling back, remove only this
callback and preserve every other redirect URI, including the pre-existing
localhost URI. Do not print or commit the client ID or secret.

The local OIDC cookie-signing secret was rotated previously. Do not restore the
former value or place any secret in source control, deployment output, or logs.

@description('Azure region for the demo application.')
param location string = 'westus'

@description('Stable environment suffix used to derive resource names.')
param environmentName string = 'rio-claro-demo'

@description('App Service plan SKU. Start with F1; B1 is only an approved fallback.')
@allowed([
  'F1'
  'B1'
])
param planSkuName string = 'F1'

@description('Name of the existing Log Analytics workspace to reuse for diagnostics.')
param logAnalyticsWorkspaceName string = 'cs-rg-rio-claro-ai901-resource-logs'

var resourceToken = uniqueString(subscription().id, resourceGroup().id, location, environmentName)
var planName = 'azasp${resourceToken}'
var appName = 'azapp${resourceToken}'
var identityName = 'azidn${resourceToken}'
var planTier = planSkuName == 'F1' ? 'Free' : 'Basic'
var planFamily = planSkuName == 'F1' ? 'F' : 'B'

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: logAnalyticsWorkspaceName
}

resource appIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: identityName
  location: location
  tags: {
    application: 'rio-claro-demo'
    managedBy: 'bicep'
  }
}

resource appServicePlan 'Microsoft.Web/serverfarms@2024-11-01' = {
  name: planName
  location: location
  kind: 'linux'
  sku: {
    name: planSkuName
    tier: planTier
    size: planSkuName
    family: planFamily
    capacity: 1
  }
  properties: {
    reserved: true
  }
  tags: {
    application: 'rio-claro-demo'
    managedBy: 'bicep'
  }
}

resource webApp 'Microsoft.Web/sites@2024-11-01' = {
  name: appName
  location: location
  kind: 'app,linux'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${appIdentity.id}': {}
    }
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    clientAffinityEnabled: false
    siteConfig: {
      alwaysOn: false
      appCommandLine: 'python3 app/startup.py'
      cors: {
        allowedOrigins: [
          'https://${appName}.azurewebsites.net'
        ]
      }
      ftpsState: 'Disabled'
      http20Enabled: true
      linuxFxVersion: 'PYTHON|3.13'
      minTlsVersion: '1.2'
    }
  }
  tags: {
    application: 'rio-claro-demo'
    managedBy: 'bicep'
  }
}

resource appDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'azdg${resourceToken}'
  scope: webApp
  properties: {
    workspaceId: logAnalyticsWorkspace.id
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

output webAppName string = appName
output appServicePlanName string = planName
output managedIdentityName string = identityName
output webAppUrl string = 'https://${appName}.azurewebsites.net'

param(
    [Parameter(Mandatory = $true)]
    [string]$ResourceGroupName,

    [Parameter(Mandatory = $true)]
    [string]$WebAppName,

    [Parameter(Mandatory = $true)]
    [string]$SubscriptionId,

    [string]$ApplicationInsightsName = 'cs-rg-rio-claro-ai901-resource-appinsights',

    [Parameter(Mandatory = $true)]
    [string]$RedirectUri,

    [switch]$ValidateOnly
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    throw 'The project virtual environment is required to load local settings safely.'
}

$settingsReader = @'
import json
import sys
import tomllib
from pathlib import Path
from dotenv import dotenv_values

root = Path(sys.argv[1])
redirect_uri = sys.argv[2]
environment = dotenv_values(root / ".env")
with (root / ".streamlit" / "secrets.toml").open("rb") as stream:
    auth = tomllib.load(stream).get("auth", {})

required_environment = (
    "DOCUMENT_INTELLIGENCE_ENDPOINT",
    "DOCUMENT_INTELLIGENCE_KEY",
    "FOUNDRY_PROJECT_ENDPOINT",
    "FOUNDRY_API_KEY",
    "FOUNDRY_MODEL",
)
values = {}
for name in required_environment:
    value = environment.get(name)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"Missing required local setting: {name}")
    values[name] = value.strip()

auth_mapping = {
    "STREAMLIT_AUTH_REDIRECT_URI": redirect_uri,
    "STREAMLIT_AUTH_COOKIE_SECRET": auth.get("cookie_secret"),
    "STREAMLIT_AUTH_CLIENT_ID": auth.get("client_id"),
    "STREAMLIT_AUTH_CLIENT_SECRET": auth.get("client_secret"),
    "STREAMLIT_AUTH_SERVER_METADATA_URL": auth.get("server_metadata_url"),
}
for name, value in auth_mapping.items():
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"Missing required local OIDC setting: {name}")
    values[name] = value.strip()

print(json.dumps(values, ensure_ascii=True))
'@

$encodedSettingsReader = [Convert]::ToBase64String(
    [System.Text.Encoding]::UTF8.GetBytes($settingsReader)
)
$settingsJson = & $python -c "exec(__import__('base64').b64decode('$encodedSettingsReader'))" $projectRoot $RedirectUri
if ($LASTEXITCODE -ne 0) {
    throw 'Could not load the required local app settings.'
}
$settings = $settingsJson | ConvertFrom-Json

if ($ValidateOnly) {
    $names = @($settings.PSObject.Properties.Name | Sort-Object)
    Write-Output "Validated required local settings: $($names -join ', ')"
    exit 0
}

$subscription = az account show --query id -o tsv
if ($LASTEXITCODE -ne 0 -or $subscription -ne $SubscriptionId) {
    throw 'Azure CLI subscription does not match the authorized subscription.'
}

$applicationInsightsResourceId = "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName/providers/Microsoft.Insights/components/$ApplicationInsightsName"
$applicationInsightsConnectionString = az resource show --ids $applicationInsightsResourceId --api-version '2020-02-02' --query properties.ConnectionString -o tsv
if ($LASTEXITCODE -ne 0 -or -not $applicationInsightsConnectionString) {
    throw 'Could not read the existing Application Insights connection string.'
}

$accessToken = az account get-access-token --resource https://management.azure.com/ --query accessToken -o tsv
if ($LASTEXITCODE -ne 0 -or -not $accessToken) {
    throw 'Could not obtain an Azure Resource Manager access token.'
}

$headers = @{
    Authorization = "Bearer $accessToken"
}
$baseUri = "https://management.azure.com/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName/providers/Microsoft.Web/sites/$WebAppName/config/appsettings"
$apiVersion = '2024-11-01'
$currentSettings = Invoke-RestMethod -Method Post -Uri "$baseUri/list?api-version=$apiVersion" -Headers $headers
$properties = @{}
if ($null -ne $currentSettings.properties) {
    foreach ($property in $currentSettings.properties.PSObject.Properties) {
        $properties[$property.Name] = $property.Value
    }
}
foreach ($property in $settings.PSObject.Properties) {
    $properties[$property.Name] = [string]$property.Value
}
$properties['APPLICATIONINSIGHTS_CONNECTION_STRING'] = [string]$applicationInsightsConnectionString
$properties['SCM_DO_BUILD_DURING_DEPLOYMENT'] = 'true'

$body = @{ properties = $properties } | ConvertTo-Json -Depth 10
$null = Invoke-RestMethod -Method Put -Uri "$baseUri`?api-version=$apiVersion" -Headers $headers -ContentType 'application/json' -Body $body

Write-Output 'App Settings updated; secret values were not emitted.'

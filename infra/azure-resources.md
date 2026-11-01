# Azure resources — deployment status

## Status: PUBLIC APP RUNNING — SCHOOL DEMO SCOPE COMPLETE

Verified on **2026-11-01 (UTC)**. Resources were deployed in West US in the
existing resource group `rg-rio-claro-ai901`; the resource group itself remains
in East US and was not changed.

| Resource | Deployed configuration | Status |
|---|---|---|
| Resource group `rg-rio-claro-ai901` | Existing group; East US | Preserved |
| User-assigned identity `azidnlh7c7u3mxydas` | West US; attached to Web App | Created |
| Linux App Service Plan `azasplh7c7u3mxydas` | Basic B1; West US | Provisioned; plan charges accrue at USD 0.018/hour |
| Linux Web App `azapplh7c7u3mxydas` | Python 3.13; HTTPS-only; West US | Running |
| Site diagnostic setting `azdglh7c7u3mxydas` | Existing Log Analytics workspace | Configured |
| Application Insights / Log Analytics | Existing resources | Reused; variable ingestion charges possible |

The public URL is <https://azapplh7c7u3mxydas.azurewebsites.net/>. It returned
HTTP 200 with valid TLS; the home page and customer catalog page loaded. The
Entra redirect URI
`https://azapplh7c7u3mxydas.azurewebsites.net/oauth2callback` is registered,
and the pre-existing localhost redirect was retained. After deploying
`streamlit[auth]==1.66.1`, the login button successfully reached the Microsoft
sign-in screen instead of raising `StreamlitMissingAuthlibError`.
On **2026-10-31**, the user completed an administrator sign-in. Selecting
**“Personal / empleados”** again after returning to Home revealed the
Administration, Invoices, and Assistant modules.
On **2026-11-01**, a navigation adjustment was deployed to open the employee
experience by default for a newly authenticated session; the user confirmed
that the correction works.

F1 provisioning failed with `QuotaExceeded` and startup failures. The B1
fallback was previewed and approved before deployment. At 730 hours, the B1
plan estimate is approximately **USD 13.14/month**. Taxes, telemetry ingestion,
and other service usage are excluded. Existing Foundry, Application Insights,
Log Analytics, and the resource group were not recreated or removed.

OneDeploy completed successfully and Oryx reported zero build errors and
warnings. The 60 unit tests passed; Bicep, parameter JSON, PowerShell syntax,
and startup code were validated. App Settings were checked by name without
emitting values.

Live service smoke tests also passed: a synthetic public-assistant question
returned an answer citing `horarios.txt`, and the project's Document
Intelligence client extracted expected fields from an in-memory synthetic
invoice. The user subsequently verified the full employee upload flow on the
deployed site, including analysis, review, confirmation, and saving to the demo
database.

The user also verified the deployed invoice workflow (analyze, review,
confirm, and save to the demo database), the employee assistant, and the
administrator messages.

**Verification note:** only the administrator account was available. The user
reports signing out of Entra ID several times and needing to authenticate
again to access protected information. Separate `obrero` and `finanzas` tests
were omitted by the user's decision; they are not reported as completed and
are not treated as pending blockers.

### Additional verification (2026-11-01 UTC)

- App Service remains `Running`; the public URL returned HTTP 200 after
  credential rotation. The replacement Document Intelligence and Foundry keys
  were verified against the active account keys without printing values. The
  OIDC cookie-signing secret was renewed; the previous service keys were
  invalidated.
- No Entra test accounts for `obrero` or `finanzas` will be provided. Per the
  user's decision, separate positive/negative tests for those roles are omitted
  from the demo scope; they are not reported as verified or as pending
  acceptance. Azure RBAC assignments are not substitutes for Entra
  application-role tests.
- The existing `rio-claro-speech` Speech resource (F0, West US) is configured
  in App Service through `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION`; setting
  values are not recorded. A fresh customer UI session displays voice
  instructions for automatic submission and playback. The user confirmed
  voice chat works in both customer and employee experiences.

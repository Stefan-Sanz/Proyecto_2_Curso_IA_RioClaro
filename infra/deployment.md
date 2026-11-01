# Deployment status — Proyecto Río Claro

## Status: PUBLIC SITE RUNNING — SCHOOL DEMO SCOPE COMPLETE

Last verified: **2026-11-01 (UTC)**.

The administrator sign-in, employee navigation, invoice flow, public assistant,
and voice chat in both audiences have been verified as recorded below. The user
also reports signing out of Entra ID several times and needing to sign in again
to access protected information.
Separate `obrero` and `finanzas` role tests were omitted by the user's decision
and are not reported as completed or as blockers.

The public site is deployed in **West US**, in the existing resource group
`rg-rio-claro-ai901` under the **Azure for Students** subscription. The group
is in East US and was not recreated or changed. The Web App is `Running` and
the public HTTPS smoke test returned HTTP 200 with valid TLS.

### Deployment decisions

- F1 provisioning failed with `QuotaExceeded` and startup failures. The
  reviewed B1 fallback was shown to the user and approved before it was
  applied.
- The Linux App Service Plan is Basic B1 at **USD 0.018/hour**, approximately
  **USD 13.14/month** at 730 hours. Taxes, telemetry ingestion, and other
  service usage are excluded.
- Existing Application Insights and Log Analytics resources are reused. The
  user accepted possible variable telemetry/ingestion charges; no new
  telemetry resources were created.
- The existing resource group, Foundry, Application Insights, and Log Analytics
  resources were not recreated or deleted.

### Deployed resources

| Resource | Configuration | Status |
|---|---|---|
| Resource group `rg-rio-claro-ai901` | Existing; East US | Preserved |
| Managed identity `azidnlh7c7u3mxydas` | User-assigned; West US | Created and attached to the Web App |
| App Service Plan `azasplh7c7u3mxydas` | Linux Basic B1; West US | Provisioned; plan charges accrue |
| Web App `azapplh7c7u3mxydas` | Linux, Python 3.13; West US; HTTPS-only | Running |
| Azure Speech `rio-claro-speech` | F0; West US | Existing resource reused; configured in App Service |
| Diagnostic setting `azdglh7c7u3mxydas` | Existing Log Analytics workspace | Configured |
| Application Insights / Log Analytics | Existing resources | Reused; variable ingestion cost possible |

### Checks and outcomes

- OneDeploy finished with **status 4 (Success)**; the remote Oryx build reported
  zero errors and warnings.
- HTTPS URL: <https://azapplh7c7u3mxydas.azurewebsites.net/> — HTTP 200 and
  valid TLS.
- The home page and the public **“Catálogo y asistente de clientes”** page
  loaded in the integrated browser.
- After Speech settings were added and the Web App restarted, a fresh browser
  session showed the voice instructions on the customer assistant page and no
  Speech-not-configured warning. The prior browser session had a disconnected
  Streamlit WebSocket; after reloading, `/_stcore/health` and
  `/_stcore/host-config` returned HTTP 200.
- A code-only 20-file ZIP redeployment completed with
  `RuntimeSuccessful` on 2026-11-01. It did not change App Settings or create
  resources. The fresh customer UI shows automatic sending when recording
  stops, attempts automatic playback, retains the audio player's manual
  controls, and no longer shows a separate **“Enviar audio”** button. The
  user manually confirmed that voice chat works in both customer and employee
  experiences, including the automatic send/playback flow.
- The Entra redirect URI
  `https://azapplh7c7u3mxydas.azurewebsites.net/oauth2callback` is registered;
  the pre-existing localhost redirect was retained.
- The deployed login button now redirects to the Microsoft sign-in page using
  the HTTPS callback; the previous `StreamlitMissingAuthlibError` no longer
  occurs; the subsequent sign-in and administrator modules were verified
  manually.
- On **2026-10-31**, the user completed Entra sign-in. The app returned to its
  home page; selecting **“Personal / empleados”** again opened the protected
  area and exposed the Administration, Invoices, and Assistant modules,
  consistent with the administrator role.
- On **2026-11-01**, the app was updated so a new authenticated session starts
  in **“Personal / empleados”**. The user has not yet retested this navigation
  after deployment; the user subsequently confirmed the navigation is fixed.
- A live Foundry request from the public customer assistant succeeded for a
  synthetic question about business hours and cited `horarios.txt`.
- A live Document Intelligence request through the project's
  `analizar_factura()` integration succeeded with an in-memory synthetic PDF.
  It extracted the synthetic invoice ID, supplier, customer, subtotal, tax,
  and total.
- The 60 unit tests passed. Bicep, parameter JSON, PowerShell syntax, and the
  startup code were validated.
- Required App Settings were checked by name only; their values were not
  emitted. The startup bootstrap writes Streamlit OIDC secrets at runtime.
- The Bicep template no longer declares the full App Settings collection;
  `infra/set-appsettings.ps1` updates settings without replacing existing
  values.
- The initial deployment omitted Streamlit's authentication extra. The
  dependency is now declared as `streamlit[auth]==1.66.1`, which installs
  Authlib, and the updated package was deployed with Oryx remote build enabled.

### Remaining acceptance checks

- Interactive Entra sign-in was tested with the available administrator
  account and the administrator modules were available. The user reports
  signing out and needing to authenticate again to access protected
  information. Per the user's decision, separate `obrero` / `finanzas` role tests
  are omitted from this demo's acceptance scope; do not report those roles as
  manually verified. Azure RBAC assignments are not substitutes for Entra
  application-role tests.
- The existing `rio-claro-speech` F0 resource and the `AZURE_SPEECH_KEY` /
  `AZURE_SPEECH_REGION` App Settings are configured in App Service; values are
  intentionally not recorded here. A fresh customer UI session displays the
  automatic-send/playback instructions. The user confirmed that voice works
  in both customer and employee experiences. Voice acceptance is complete
  based on that manual confirmation.
- The ZIP deployment completed successfully on 2026-11-01 at 03:34 UTC. The
  20-file package contained only `app/`, `data/`, and `requirements.txt`;
  `.env`, Streamlit secrets, `.demo-data`, tests, and bytecode were excluded.
  The existing App Service settings and demo database were preserved.
- The subsequent voice UX ZIP contained the same 20-file allowlist; it was
  deployed to the existing Web App without changing its settings or resources.
- The user verified the deployed employee invoice flow: a file was analyzed,
  reviewed, confirmed, and saved to the local demonstration database.
- This manual end-to-end invoice test supersedes the earlier synthetic
  Document Intelligence client-only smoke test; the employee upload flow is
  now verified.
- After successful Entra callback, the app returns to the home page and the
  user previously had to select **“Personal / empleados”** again. This was
  changed so newly authenticated sessions open the employee experience
  automatically; the user confirmed the correction.
- Telemetry ingestion and any service usage charges have not been measured.

### Credential rotation verification

During the deployment review, the service keys for `PracticaDocuments1` and
`cs-rg-rio-claro-ai901-resource` were rotated to their replacement keys and the
previous keys were invalidated after health checks. The OIDC cookie-signing
secret was also renewed. App Settings were updated without recording their
values; an in-memory comparison confirmed the configured service keys match
the active replacements. The public site returned HTTP 200 and App Service
reported `Running` after rotation. Existing OIDC sessions were invalidated
and users must sign in again. No client secret was changed.

### Deployment fixes

- Oryx could not find the original bootstrap under `infra/`; it now runs
  `python3 app/startup.py`, inside the published application tree.
- Bicep initially replaced the App Settings collection. The template now
  leaves that collection unmanaged, and the settings helper preserves existing
  values while applying the required configuration.

The public deployment and school demo scope are operational. The user reports
that signing out requires authentication again to access protected
information. The other-role tests are intentionally omitted by the user's
decision, not pending acceptance work. Live service and other completed checks
are recorded above.

### Security follow-up

The local OIDC cookie-signing secret was rotated after it was rendered during
a prior inspection. The replacement value was not emitted and must not be
committed or copied into deployment logs.

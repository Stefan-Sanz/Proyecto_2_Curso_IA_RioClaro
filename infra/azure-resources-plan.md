# Recursos Azure — alcance y estado escolar

Este archivo distingue los servicios integrados, desplegados y fuera del
alcance; no presupone que los datos sintéticos sean operativos.

## Integrados en la aplicación

- **Azure AI Foundry:** modelo configurado para el asistente.
- **Azure AI Document Intelligence:** análisis `prebuilt-invoice` para los archivos de ejemplo cargados en la demo; se reutiliza el recurso existente `PracticaDocuments1`.
- **Microsoft Entra ID:** la aplicación usa OIDC y autorización por roles para el personal. «Estado del pedido» usa acceso genérico simulado, sin Entra ID ni verificación de identidad, y solo consulta datos sintéticos locales. No usarlo para pedidos reales.
- **Azure Speech:** captura, transcripción y lectura de voz están integradas.
  Se reutiliza el recurso existente `rio-claro-speech` (F0, West US), con
  `AZURE_SPEECH_KEY` y `AZURE_SPEECH_REGION` configuradas sin registrar sus
  valores. El usuario confirmó manualmente que el chat de voz funciona en las
  experiencias de clientes y empleados, incluido el envío al detener la
  grabación y el intento de reproducción automática. El audio de entrada no se
  persiste en la aplicación. No se aprovisionó otro recurso; el uso puede
  generar cargos variables.

## Desplegado

- **Azure App Service:** Linux Basic B1 en West US dentro del grupo existente
  `rg-rio-claro-ai901`; la aplicación publicada está en ejecución. La URL HTTPS
  y los límites de aceptación están registrados en `deployment.md`.

## Servicios no usados

- **Azure AI Search:** no participa en el análisis de facturas. Podría utilizarse para recuperación documental, pero el chat actual usa archivos locales y no requiere Search.
- **Azure Storage y base de datos empresarial:** no se usan. La aplicación puede guardar campos revisados de facturas en una SQLite local de demostración; no se aprovisiona ningún recurso Azure para esto.

## Identidad de prueba

La aplicación tiene autorización por roles en código, pero no hay cuentas
Entra de prueba disponibles para `obrero` y `finanzas`. No se crearon usuarios
ni se cambiaron roles durante esta revisión. Por decisión del usuario, no se
proporcionarán cuentas separadas y las pruebas manuales positivas/negativas
para esos roles se omiten del alcance de la demostración; no se reportan como
roles verificados. Las asignaciones Azure RBAC no sustituyen los roles de
aplicación Entra.

No aprovisionar recursos ni asumir costos sin aprobación. Confirmar recursos,
región y cuotas en Azure antes de cualquier despliegue.

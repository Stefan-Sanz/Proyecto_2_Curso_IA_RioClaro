# Diario del proyecto Río Claro

Este diario resume la evolución documentada de la demostración. Las fechas no
incluidas en las notas de origen se dejan sin asignar. El estado actual y sus
límites se consolidan en [avance-proyecto.md](./avance-proyecto.md).

## Etapa inicial — fecha no especificada

- Preparación de VS Code, instalación de extensiones y creación de la
  estructura del proyecto y documentación inicial.
- Creación del grupo de recursos existente `rg-rio-claro-ai901` en East US.
- Configuración del entorno Python, entorno virtual, dependencias y primera
  aplicación Streamlit ejecutable localmente.
- Reutilización del recurso existente `PracticaDocuments1` para Azure AI
  Document Intelligence. Las credenciales se configuran fuera del código.
- Primera integración para cargar PDF, enviar el archivo al servicio y mostrar
  el texto extraído.
- Incorporación del modelo `prebuilt-invoice` y extracción estructurada de
  campos de factura. La extracción no elimina la revisión humana ni demuestra
  una reducción medida de trabajo manual.
- Pruebas de acceso a Azure AI Foundry y desarrollo del asistente en español
  integrado con Streamlit.

## Hitos funcionales — fechas no especificadas en las notas iniciales

- Se completaron los flujos de facturas y asistentes, y se añadieron formatos
  PDF, JPG, JPEG y PNG.
- Se separaron las experiencias de clientes y personal, con documentos
  permitidos por audiencia y rol.
- Se incorporaron catálogo e inventario local de solo lectura y pedidos
  sintéticos. Estos datos no representan operaciones reales.
- Se añadió confirmación humana para los campos de factura que lo requieren y
  guardado explícito de campos en SQLite local de demostración. No se conserva
  el archivo original.

## Validaciones manuales — 31 de octubre de 2026

- Se validaron navegación entre Inicio y las experiencias disponibles, filtro
  del catálogo, consulta de pedidos sintéticos y botones del flujo de facturas.
- Los asistentes de clientes y personal respondieron preguntas de catálogo y
  políticas con los permisos de la cuenta disponible.
- Se validó que la consulta de pedidos pide número y nombre sintéticos y
  responde con datos de `pedidos_demo.json`; no autentica a la persona.
- Una revisión de confianza baja permitió editar y guardar los campos antes
  de confirmar la factura. No se compartieron datos de factura en la evidencia.
- El usuario confirmó que el chat de voz funciona en clientes y empleados:
  transcripción al asistente correspondiente, envío al detener la grabación e
  intento de reproducción automática. La aplicación no persiste el audio de
  entrada.
- Por decisión del usuario, no se realizaron pruebas separadas de los roles
  `obrero` y `finanzas`; no se consideran roles validados.
- El usuario confirmó que cerró sesión de Entra ID en varias ocasiones y tuvo
  que autenticarse de nuevo para volver a acceder a la información protegida.

## Publicación y verificaciones — 1 de noviembre de 2026 UTC

- El aprovisionamiento inicial Free F1 falló por cuota y problemas de arranque.
  Tras revisión y aprobación del `what-if`, se publicó en Azure App Service
  Linux Basic B1 en West US.
- El App Service quedó en estado `Running`; el sitio público y su endpoint de
  salud respondieron HTTP 200. El costo estimado del plan B1 es USD 0.018 por
  hora, aproximadamente USD 13.14 por 730 horas, excluyendo telemetría,
  impuestos y otros servicios.
- Se corrigió la dependencia de Authlib, la ruta de arranque de Oryx y la
  preservación de App Settings durante la publicación.
- Se verificaron llamadas reales a Foundry y Document Intelligence con
  preguntas o archivos sintéticos. La documentación de despliegue registra
  60 pruebas unitarias aprobadas con servicios simulados.
- Se verificó el inicio de sesión con la cuenta administradora y se ajustó la
  navegación para abrir Personal tras la autenticación. El usuario también
  confirmó que cerró sesión y tuvo que volver a autenticarse para acceder a la
  información protegida. No se afirman pruebas de otros roles.
- Se reutilizó Azure Speech F0 existente; no se aprovisionó otro recurso. La
  ingesta de telemetría y los cargos variables no han sido medidos.

## Estado final

- El usuario confirmó que cerró sesión de Entra ID y tuvo que volver a
  autenticarse para acceder a la información protegida.
- Las pruebas separadas de `obrero` y `finanzas` se omitieron por decisión del
  usuario y no son tareas pendientes del alcance acordado.
- El informe y el código son las evidencias documentales y técnicas. El usuario
  prepara por separado el PPT y tomará allí capturas de la aplicación; no son
  entregables pendientes de este repositorio.
- El equipo de trabajo está compuesto por el usuario responsable del proyecto
  y el asistente de IA como apoyo técnico y documental.

Las fechas de despliegue se conservan en UTC; no deben presentarse como fechas
locales verificadas.

# Informe de avance — Proyecto Río Claro

## Resumen ejecutivo

Río Claro cuenta con una demostración escolar en Streamlit que reúne el
procesamiento de facturas, asistentes para clientes y personal, catálogo,
inventario y pedidos sintéticos. La aplicación está desplegada en Azure App
Service Linux Basic B1. La evidencia disponible incluye respuestas HTTP 200,
pruebas unitarias, llamadas reales a Foundry y Document Intelligence, y
validaciones manuales de los flujos principales.

El proyecto no es un sistema empresarial ni productivo. El alcance escolar y
los flujos principales están completados según las evidencias disponibles. El
usuario confirma que cerró sesión de Entra ID en varias ocasiones y tuvo que
autenticarse de nuevo para volver a acceder a la información protegida. Las
pruebas separadas de los roles `obrero` y `finanzas` se omitieron por decisión
del usuario y no se reportan como realizadas. No se han medido beneficios de
negocio ni precisión con datos empresariales.

## Avance e hitos

| Hito | Resultado documentado | Evidencia y estado |
|---|---|---|
| Entorno y aplicación inicial | Entorno Python, dependencias y primera interfaz Streamlit ejecutable localmente. | Registrado en el diario del proyecto; fecha de esta etapa no especificada. |
| Extracción de facturas | Integración con Azure AI Document Intelligence para PDF e imágenes; extracción de campos con `prebuilt-invoice`. Se requiere revisión humana para los campos definidos con confianza menor a 80% o sin confianza. | El flujo desplegado de análisis, revisión, confirmación y guardado fue validado manualmente. El archivo fuente no se conserva en SQLite. |
| Asistentes y conocimiento | Asistentes separados para clientes y personal, conectados a Azure AI Foundry. Usan archivos locales permitidos para cada audiencia/rol; las referencias se limitan a archivos enviados al modelo. | Pruebas manuales registradas para preguntas de catálogo y políticas. Se registró una consulta real sobre horarios con referencia a `horarios.txt`. |
| Funciones demostrativas | Catálogo e inventario de solo lectura y pedidos sintéticos locales. El acceso genérico a pedidos no verifica identidad. | Se validaron filtros, consulta de pedido sintético y navegación. Los datos no representan operaciones reales. |
| Chat de voz | Azure Speech transcribe la pregunta y la pasa al asistente correspondiente; al detener la grabación se envía automáticamente. La aplicación intenta reproducir la respuesta y conserva un reproductor manual alternativo. | El usuario confirmó manualmente que funciona en clientes y empleados. La aplicación no persiste el audio de entrada. Se reutiliza el recurso Speech F0 existente. |
| Pruebas y preparación | Suite unitaria aprobada con servicios simulados; la documentación de despliegue registra 60 pruebas aprobadas. | Las pruebas unitarias no demuestran disponibilidad de Azure ni precisión empresarial. |
| Publicación escolar | App Service Linux Basic B1 en West US, aplicación en ejecución y sitio HTTPS con respuesta HTTP 200. | Verificación de despliegue registrada el 1 de noviembre de 2026 UTC. El usuario confirmó haber cerrado sesión varias veces y necesitar iniciar sesión de nuevo para acceder a la información protegida. |

## Resultados funcionales

- **Facturas:** análisis de PDF o imagen, visualización de campos y revisión
  humana. Los campos confirmados como vigentes pueden guardarse explícitamente
  en SQLite local de demostración; no se guarda el archivo original.
- **Asistentes:** chat de clientes y chat interno con contexto y permisos
  separados. El cliente no recibe documentos internos; el personal conserva la
  autorización por rol.
- **Voz:** entrada en español y lectura hablada de respuestas mediante el
  asistente existente, sin crear un agente paralelo ni cambiar sus permisos.
  La aplicación no persiste el audio de entrada.
- **Catálogo e inventario:** consultas de muestra a archivos locales de solo
  lectura.
- **Pedidos:** consulta de ejemplos sintéticos usando número y nombre de prueba;
  no se conecta a un sistema real ni autentica a la persona.
- **Publicación:** despliegue público verificado y flujos principales probados
  según la evidencia registrada en `infra/deployment.md`.

## Retos y soluciones aplicadas

| Reto o punto crítico | Solución aplicada | Situación |
|---|---|---|
| El plan Free F1 no pudo aprovisionarse por cuota y fallos de arranque. | Se presentó un `what-if`, se obtuvo aprobación y se publicó en Basic B1. | Resuelto. El costo estimado del plan es USD 0.018/h (aprox. USD 13.14 por 730 horas), sin impuestos, telemetría ni otros servicios. |
| El primer despliegue no instaló Authlib y el inicio de sesión falló. | Se declaró `streamlit[auth]==1.66.1` y se volvió a desplegar. | Resuelto para el inicio de sesión probado con la cuenta administradora. |
| Oryx no encontraba el arranque en la ruta anterior. | Se ajustó el comando para ejecutar `python3 app/startup.py` dentro del paquete publicado. | Resuelto y registrado en la documentación de despliegue. |
| La plantilla Bicep podía reemplazar la colección completa de App Settings. | Se dejó esa colección fuera de la administración de Bicep y el script de configuración conserva valores existentes. | Resuelto; no se registran valores secretos en la documentación. |
| Después del callback Entra, el usuario debía volver a elegir la experiencia de personal. | Se ajustó la navegación de una sesión autenticada nueva para abrir Personal. | El usuario confirmó la corrección. |
| Una interacción de Enter en la revisión de factura podía enviar o guardar campos pendientes. | Se separó la edición de la confirmación explícita y se probó la revisión con confianza baja. | Validado manualmente; la persona puede editar, guardar y confirmar. |
| La demo podía confundirse con un sistema operativo real. | Se etiquetaron los pedidos, catálogo e inventario como sintéticos; se limitaron las referencias y se documentaron SQLite, la revisión humana y la ausencia de métricas reales. | Control documental y de interfaz. |

## Puntos críticos y límites

- **Identidad:** el inicio de sesión y la experiencia administrativa se
  verificaron con la cuenta disponible. El usuario reporta cierres de sesión
  de Entra ID en varias ocasiones y que tuvo que autenticarse nuevamente para
  acceder a la información protegida. Las pruebas separadas de `obrero` y
  `finanzas` se omitieron por decisión del
  usuario; no son evidencia de que esos roles hayan funcionado o fallado.
- **Costos:** el plan B1 tiene un costo estimado de USD 13.14 por 730 horas.
  La ingesta de telemetría y el uso de servicios pueden generar cargos
  variables que no se han medido. Se reutiliza el recurso Speech F0 existente;
  no se aprovisionaron recursos adicionales de voz.
- **Facturas:** la extracción no garantiza exactitud. La confirmación humana es
  necesaria y SQLite es local, de demostración y no constituye una auditoría ni
  un reporte financiero.
- **Conocimiento:** los documentos locales se envían completos al modelo; no
  hay Azure AI Search ni recuperación por relevancia. Las referencias son
  nombres de archivos, no citas verificadas de fragmentos.
- **Datos:** catálogo, inventario y pedidos son sintéticos. No hay integración
  con ERP, pedidos reales ni inventario operativo.
- **Resultados de negocio:** no se midieron reducción de captura, ahorro de
  tiempo, tasa de errores ni precisión con datos empresariales.
- **Responsible AI:** el documento de controles y límites no es una auditoría
  ni una evaluación formal de impacto.

## Estado final y verificaciones no realizadas

- **Cierre de sesión:** el usuario informa que cerró sesión de Entra ID en
  varias ocasiones y tuvo que volver a iniciar sesión para acceder a la
  información protegida. Esta es evidencia de uso reportada por el usuario.
- **Roles `obrero` y `finanzas`:** las pruebas separadas se omitieron por
  decisión del usuario. No son trabajo pendiente dentro del alcance acordado
  ni evidencia de que esos roles hayan sido validados.
- **Métricas y costos variables:** no se midieron beneficios de negocio,
  ingesta de telemetría ni cargos variables por uso. Se reportan como límites,
  no como resultados.
- **Presentación:** el informe y el código del proyecto constituyen las
  evidencias documentales y técnicas disponibles. El usuario prepara por
  separado el PPT y tomará allí las capturas de la aplicación en funcionamiento;
  esas capturas no están pendientes en este repositorio.
- **Equipo de trabajo:** el usuario, responsable de las decisiones, pruebas y
  presentación, y el asistente de IA, como apoyo técnico y documental.

## Fechas y fuentes

Este informe distingue la fecha local de la sesión (31 de octubre de 2026,
UTC-6) de las verificaciones registradas con fecha **1 de noviembre de 2026
UTC**. Estas últimas se mantienen como fechas UTC y no se atribuyen como fechas
locales verificadas.

Fuentes principales: `docs/plan-trabajo.md`, `docs/diario-proyecto.md`,
`infra/deployment.md`, `infra/azure-resources.md` y `infra/rollback.md`.

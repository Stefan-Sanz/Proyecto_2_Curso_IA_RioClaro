# Proyecto final AI-901 — Río Claro

## Equipo de trabajo

- Usuario responsable del proyecto: decisiones, validaciones manuales y
  presentación.
- Asistente de IA (Copilot SDK en VS Code): apoyo técnico y documental.

## Caso de negocio
La demostración escolar ilustra dos necesidades del caso Río Claro:

Automatizar la captura de facturas.
Implementar un asistente inteligente.
## Solución demostrada

### Módulo 1 — Procesamiento de facturas

Azure AI Document Intelligence analiza PDF o imágenes de muestra. Los campos
identificados incluyen proveedor, RFC de proveedor/cliente, cliente, folio,
subtotal, IVA y total. Los campos definidos con confianza inferior a 80% o sin
confianza requieren confirmación humana. Después de confirmar una factura como
vigente, se pueden guardar explícitamente sus campos en SQLite local de
demostración; el archivo original no se almacena.

### Módulo 2 — Asistentes de clientes y personal

Azure AI Foundry y el modelo configurado por `FOUNDRY_MODEL` proporcionan
respuestas en español. Clientes acceden sin iniciar sesión y solo reciben
contexto público autorizado. El asistente interno requiere Microsoft Entra ID y
usa documentos permitidos por rol. Las referencias son nombres de archivos
enviados, no citas de fragmentos recuperados.

Ambos asistentes admiten chat de voz mediante Azure Speech: transcripción en
español al asistente correspondiente y lectura hablada de la respuesta. El
usuario confirmó manualmente el flujo en clientes y empleados. Se reutiliza el
recurso F0 existente; el audio de entrada no se conserva en la aplicación.

### Módulo 3 — Catálogo, inventario y pedidos de muestra

El catálogo y el inventario son archivos locales de solo lectura. El seguimiento
usa pedidos sintéticos y un acceso genérico que no verifica identidad; no hay
conexión con sistemas operativos.

### IA responsable

Consultar [responsible-ai.md](./responsible-ai.md). El documento describe
controles y límites, no una auditoría formal ni una evaluación de impacto.

## Resultados y estado

La aplicación está desplegada en Azure App Service Linux Basic B1 en West US.
El sitio público respondió HTTP 200 en la verificación registrada el 1 de
noviembre de 2026 UTC. Se documentaron 60 pruebas unitarias aprobadas con
servicios simulados y verificaciones manuales de los flujos principales.
El costo estimado del plan es USD 0.018/h (aprox. USD 13.14 por 730 horas), sin
incluir impuestos, telemetría u otros servicios.

La demostración ilustra extracción documental y consulta de información de
muestra. No se midió reducción de captura manual, ahorro de tiempo, tasa de
errores ni precisión con datos empresariales.

Alcance y limitaciones

- El análisis de facturas usa Azure AI Document Intelligence; los archivos deben ser de ejemplo o autorizados.
- El asistente usa Azure AI Foundry y archivos de conocimiento locales de muestra. No utiliza Azure AI Search; muestra referencias a los archivos que el modelo identifica como respaldo, limitadas a los documentos enviados y sin citas de fragmentos.
- El asistente de clientes no recibe documentos internos; su historial se separa del asistente interno.
- Catálogo e inventario son datos de juguete; el seguimiento usa pedidos sintéticos locales y acceso genérico simulado, no una autenticación real.
- Solo proveedor, RFC de proveedor/cliente, cliente, folio, subtotal, total e IVA se evalúan para confianza; valores inferiores a 80% o sin confianza requieren confirmación humana. Las facturas confirmadas como vigentes pueden guardarse explícitamente en una SQLite local de demostración; no es auditoría persistente ni reporte oficial.
- El usuario confirmó que cerró sesión de Entra ID varias veces y tuvo que volver a iniciar sesión para acceder a la información protegida. Por decisión del usuario, se omiten pruebas separadas de `obrero` y `finanzas`; no se reportan como realizadas ni como roles validados.
- Se reutiliza el recurso Azure Speech F0 existente. La ingesta de telemetría y los costos variables por uso no se han medido.
- Los registros de despliegue fechados 1 de noviembre de 2026 corresponden a UTC y no se presentan como fechas locales verificadas.

Consulta el [informe de avance](./avance-proyecto.md) para hitos, retos,
soluciones, fuentes y pendientes.
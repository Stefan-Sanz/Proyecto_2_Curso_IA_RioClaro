Guion de Presentación
Introducción
Buenos días.

Presentamos la solución desarrollada para el caso de negocio Río Claro.

El caso de negocio plantea dos necesidades que esta demostración escolar ilustra:

Captura manual de facturas.
Consultas frecuentes de empleados y clientes.
Solución
Desarrollamos una aplicación web con Streamlit y servicios de Azure AI.

La demostración cuenta con:

Procesamiento automático de facturas.
Experiencias separadas para clientes y personal.
Catálogo y documentos locales de muestra.
Página principal
Mostrar «Bienvenidos a la página de Rio Claro» y las opciones de clientes y personal/empleados.
Módulo Clientes
Demostración:

Consultar el catálogo sin iniciar sesión.
Hacer una pregunta al asistente de clientes sin iniciar sesión.
Si el recurso Azure Speech está disponible, grabar una pregunta, detener la
grabación para que se envíe al asistente y mostrar la respuesta hablada. Si el
navegador bloquea la reproducción automática, iniciar el reproductor manual.
Abrir «Estado del pedido» e iniciar la sesión genérica de demostración con el nombre «Ana López».
Consultar el pedido sintético `RC-DEMO-1001` y aclarar que escribir el nombre no verifica identidad y que todos los datos de pedidos son ficticios.
Módulo Personal / empleados
Demostración:

Iniciar sesión con Entra ID y acceder únicamente a los módulos permitidos por el rol.
Consultar el asistente interno con documentos autorizados para ese rol.
No afirmar que los roles o cuentas de prueba funcionan hasta verificar el tenant.
La validación disponible corresponde a la cuenta administradora. Las pruebas
separadas de `obrero` y `finanzas` se omitieron por decisión del usuario.
Módulo Facturas
Demostración:

Cargar PDF.
Extraer información automáticamente.
Aclara que Document Intelligence extrae campos automáticamente, pero la demo no mide reducción de trabajo ni tasa de errores.
Asistente con contexto documental
Demostración:

Catálogo público para clientes.
Documentos internos autorizados por rol para empleados.
Horarios.
Políticas de devolución.
Cada asistente recibe solo el contexto permitido para su audiencia. No usa Azure AI Search; el catálogo y el inventario son datos de juguete.
Al responder, cada asistente puede mostrar los nombres de los archivos que el modelo identifica como respaldo. La aplicación solo acepta referencias a los archivos que sí recibió; estas referencias no son citas de fragmentos.
Mostrar la nota: «Estás chateando con una IA. Sus respuestas pueden contener errores; verifica la información importante.»

Responsible AI
La solución considera estos principios; no se realizó una evaluación formal de impacto:

Equidad
Confiabilidad
Privacidad
Inclusión
Transparencia
Responsabilidad
Conclusiones
La demostración permite observar la extracción de campos y consultar información local de muestra. No se presentan métricas de reducción de tiempos o errores, pues no se ha evaluado un proceso real.

Alcance por mencionar

- Document Intelligence procesa el archivo de ejemplo enviado durante la demostración.
- Los pedidos son sintéticos y el acceso por nombre no verifica identidad.
- Proveedor, RFC, cliente, folio, subtotal, total e IVA con confianza menor a 80% deben confirmarse antes de validar la factura; el guardado en SQLite es local y solo para la demostración.
- La aplicación integra voz con Azure Speech para transcribir preguntas y leer respuestas; el usuario confirmó que funciona en las experiencias de clientes y empleados. La grabación se envía al detenerla y la respuesta intenta reproducirse automáticamente. Se reutiliza el recurso F0 existente y el audio de entrada no se guarda en la aplicación.
- No hay base de datos empresarial: la SQLite es local y solo para la demostración. La aplicación sí está desplegada públicamente en Azure App Service.
- El plan App Service Linux Basic B1 en West US cuesta aproximadamente USD 13.14 por 730 horas; telemetría, impuestos y otros servicios no están incluidos. No se han medido los cargos variables.
- El usuario confirmó que cerró sesión de Entra ID en varias ocasiones y tuvo que iniciar sesión de nuevo para acceder a la información protegida. Las fechas de publicación registradas como 1 de noviembre de 2026 son UTC.
Gracias.
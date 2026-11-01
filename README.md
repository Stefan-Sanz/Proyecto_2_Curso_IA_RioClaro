---
Proyecto Río Claro - AI-901
Descripción
Proyecto desarrollado como solución para el caso de negocio Río Claro.

La solución es una demostración escolar que utiliza Azure AI Document Intelligence para extraer campos de archivos de factura de ejemplo y Azure AI Foundry para asistentes que consultan documentos locales de muestra autorizados para cada audiencia.

La página inicial muestra «Bienvenidos a la página de Rio Claro» y separa la experiencia de clientes de la de personal/empleados. El catálogo y el asistente de clientes son públicos; el seguimiento de pedidos usa un acceso genérico simulado y solo consulta pedidos sintéticos.

Capacidades demostradas
1. Captura automática de facturas
El módulo permite demostrar la extracción sobre un PDF o imagen de ejemplo o autorizado para la demostración.

La solución:

Procesa documentos automáticamente.
Extrae información relevante.
No se ha medido una reducción de captura manual en un proceso real.
Campos detectados:

Proveedor
RFC Proveedor
Cliente
RFC Cliente
Folio
IVA
Subtotal
Total
2. Asistentes de clientes y personal
Se implementaron asistentes basados en Azure AI Foundry y el modelo configurado.

Capacidades:

Respuestas en español.
Asistente de clientes con contexto público aprobado.
Asistente interno con contexto limitado por rol.
3. Consulta de documentos de muestra
El asistente utiliza archivos locales de juguete para responder preguntas relacionadas con:

Inventario
Horarios
Políticas de devolución
Arquitectura
Frontend
Streamlit
Servicios Azure
Azure AI Foundry
Modelo configurado mediante `FOUNDRY_MODEL`
Azure AI Document Intelligence
Inteligencia Artificial
OCR
Extracción de información
IA Generativa
Contexto documental local enviado al modelo (sin Azure AI Search ni recuperación por relevancia)
Estructura del proyecto
app/
data/
docs/
infra/
tests/
Principios de IA Responsable
Equidad
Confiabilidad
Privacidad
Transparencia
Inclusión
Responsabilidad
Estado
Demostración funcional local cuando están configurados los servicios Azure requeridos.

## Ejecución local

Usa Python 3.13 y las versiones fijadas en `requirements.txt`:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\streamlit.exe run app/main.py
```

Configura en `.env` (o en la configuración del servicio) las variables
`DOCUMENT_INTELLIGENCE_ENDPOINT`, `DOCUMENT_INTELLIGENCE_KEY`,
`FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_API_KEY` y `FOUNDRY_MODEL`.
La aplicación muestra los nombres de las variables faltantes, nunca sus valores.
Para habilitar el chat de voz, configura además `AZURE_SPEECH_KEY` y
`AZURE_SPEECH_REGION`. Esta configuración es opcional: sin ella los asistentes
siguen disponibles por texto. La demostración reutiliza el recurso Azure
Speech F0 existente `rio-claro-speech`; la aplicación no aprovisiona recursos.
El uso del servicio puede generar cargos variables.

## Pruebas

Las pruebas usan servicios simulados y no necesitan credenciales de Azure:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Catálogo e inventario

El catálogo de solo lectura se consulta desde `data/catalogo_productos_rio_claro.txt`;
la experiencia de clientes permite filtrar por categoría mediante botones.
El inventario también es de solo lectura y usa `data/inventario.txt`: el rol
`obrero` puede buscar productos, elegir una sucursal o consultar el consolidado.
Las existencias no registradas se muestran como “Sin dato”, sin asumir que sean cero.

El catálogo y el inventario son datos locales de juguete; no representan precios
ni existencias operativas.
En la experiencia de clientes, las categorías del catálogo se muestran como
botones junto al asistente.

En la pantalla de facturas, solo proveedor, RFC del proveedor y del cliente,
cliente, folio, subtotal, total e IVA se evalúan para confianza. Si la confianza
de uno de estos campos es inferior a 80% —o no está disponible— requiere
confirmación humana antes de confirmar la factura como vigente. «Guardar datos»
conserva las correcciones en la sesión; «Confirmo que los datos son correctos»
confirma la factura como vigente. La confianza es una señal, no una garantía
de exactitud. Después se pueden guardar campos y confianzas en una base SQLite local de demostración en
`.demo-data/facturas.sqlite3`. No se guarda el archivo original. La carpeta está
excluida de Git; usa únicamente facturas sintéticas o autorizadas y elimina la
base local al terminar la demostración. No sustituye una auditoría ni produce
reportes financieros oficiales.

El seguimiento de pedidos usa un acceso genérico de demostración que solo pide
un nombre; no verifica identidad ni protege datos. La pantalla consulta
exclusivamente ejemplos ficticios de `data/pedidos_demo.json`, comparando el
número del pedido y el nombre. Si se pregunta por el seguimiento sin ambos datos,
el chat solicita el número sintético y el nombre completo del cliente de prueba;
con ambos puede responder el estado. Estos ejemplos no representan pedidos
reales y no deben mezclarse con información personal u operativa.

El chat muestra conversaciones separadas para clientes y personal, y envía al
modelo hasta los últimos diez mensajes de cada conversación (cinco turnos). El
asistente de clientes solo recibe catálogo, horarios y política de devoluciones;
el asistente interno recibe los archivos locales permitidos por rol. Se solicita
al modelo que cite los archivos que respaldan directamente cada respuesta; la
aplicación restringe las referencias a los nombres de documentos realmente
enviados. Son referencias a archivos, no citas de fragmentos. El contexto se
envía completo al modelo; no se usa Azure AI Search ni recuperación por
relevancia. Ambos chats advierten que la IA puede cometer errores.

Con Azure Speech configurado, ambas experiencias permiten grabar una pregunta,
que se envía automáticamente al detener la grabación para transcribirla en
español y pasar el texto al asistente existente con su mismo historial, rol y
contexto. La aplicación intenta reproducir automáticamente la respuesta; si el
navegador lo bloquea, el reproductor permite iniciarla manualmente. El audio de
entrada no se guarda en archivos ni en el historial. El chat de voz fue
confirmado manualmente por el usuario en clientes y empleados. Se reutiliza el
recurso Azure Speech F0 existente `rio-claro-speech`; no se aprovisionó otro
recurso. El uso del servicio puede generar cargos variables.

## Acceso de usuarios

El catálogo y el asistente de clientes están disponibles sin iniciar sesión. El
seguimiento de pedidos usa acceso genérico simulado para una experiencia
exclusivamente ficticia; escribir un nombre no autentica a la persona. La
experiencia de personal requiere Microsoft Entra ID y un rol interno.

La autenticación usa el soporte OIDC integrado de Streamlit. Configura el claim
`roles` con los valores `cliente`, `obrero`, `finanzas` y `administrador`, y asigna
solo los roles aprobados a cada usuario. Para desarrollo, registra
`http://localhost:8501/oauth2callback` como URL de redirección y agrega la URL
HTTPS si se publica en Azure. Confirma los claims, usuarios asignados y redirección
en el tenant de Entra antes de la demo.

Crea `.streamlit/secrets.toml` localmente (no lo agregues al repositorio):

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "<secreto aleatorio largo>"
client_id = "<id de aplicación de Entra ID>"
client_secret = "<secreto de aplicación de Entra ID>"
server_metadata_url = "https://login.microsoftonline.com/<tenant-id>/v2.0/.well-known/openid-configuration"
```

La autorización también se valida en los servicios. Finanzas y administración
pueden procesar facturas; obreros pueden consultar existencias. La autenticación
simulada de pedidos no sirve como control de acceso y nunca debe reutilizarse
para una fuente real. Los pedidos de muestra se consultan únicamente desde el
archivo sintético incluido.

## Alcance y estado de la demostración

La aplicación está publicada en Azure App Service Linux Basic B1 en West US:
<https://azapplh7c7u3mxydas.azurewebsites.net/>. En la verificación registrada
el 1 de noviembre de 2026 UTC, el sitio respondió HTTP 200. El costo estimado
del plan es USD 0.018/h (aprox. USD 13.14 por 730 horas), sin incluir
telemetría, impuestos ni otros servicios. La ingesta de telemetría y el uso
variable no se han medido.

Foundry, Document Intelligence y Azure Speech son servicios usados por la
aplicación cuando están configurados. Se reutiliza el recurso Azure Speech F0
existente; cualquier consumo puede generar cargos. No se aprovisionó un nuevo
recurso de voz. Los pedidos sintéticos y la base SQLite local son
demostraciones, no servicios de negocio. Azure AI Search no participa en el
análisis de facturas ni está integrado en la consulta documental actual.

El inicio de sesión y la experiencia de administración se verificaron con la
cuenta disponible. El usuario confirmó que cerró sesión de Entra ID varias
veces y tuvo que volver a autenticarse para acceder a la información protegida.
Por decisión del usuario, no se realizaron pruebas separadas para `obrero` y `finanzas`; no se
reportan como roles validados. La aplicación no tiene base de datos empresarial
ni pedidos reales, y solo guarda campos de factura en SQLite local de
demostración cuando se solicita.

Consulta el [informe de avance](docs/avance-proyecto.md) y el
[estado detallado del despliegue](infra/deployment.md) para resultados,
pendientes y límites.
---
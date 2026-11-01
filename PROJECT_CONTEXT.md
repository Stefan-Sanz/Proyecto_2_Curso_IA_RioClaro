Proyecto Río Claro - Contexto Oficial
# Proyecto Río Claro — contexto de implementación

## Objetivo escolar

Demostrar dos capacidades con una aplicación Streamlit:

1. Extraer campos de una factura de ejemplo usando Azure AI Document Intelligence.
2. Consultar documentos locales de muestra mediante un asistente conectado a Azure AI Foundry.

La demostración no es un sistema empresarial ni presupone que existan facturas reales, pedidos, inventario operativo o una base de datos.

## Tecnologías y datos

- Python y Streamlit.
- Azure AI Document Intelligence (`prebuilt-invoice`) para los archivos que se cargan en la demo.
- Azure AI Foundry y el modelo indicado por `FOUNDRY_MODEL` para el chat.
- Microsoft Entra ID/OIDC y autorización por roles para las funciones protegidas.
- Catálogo, inventario y conocimiento cargados desde archivos de texto locales en `data/`; son datos de juguete.

Azure AI Search no está integrado y no interviene en el análisis de facturas. El contexto documental actual se compone de archivos locales permitidos por rol, sin recuperación por relevancia ni citas. Azure Speech tampoco está integrado; la voz es una posible ampliación que requiere implementación en la aplicación y configuración del servicio.

## Estado funcional

- Facturas: carga de PDF/JPG/JPEG/PNG y extracción en vivo por Document Intelligence. Los estados de factura y señales de posible duplicidad son temporales en la sesión.
- Asistente: chat en español con Foundry, contexto documental local y acceso limitado por rol.
- Catálogo e inventario: búsqueda y filtros de muestra, solo lectura.
- Pedidos y administración: pantallas/mensajes demostrativos; no consultan ni modifican sistemas reales.
- Pruebas: las pruebas unitarias emplean servicios simulados; no demuestran disponibilidad de Azure ni precisión con datos empresariales.

## No incluido en el alcance

Base de datos, almacenamiento persistente, pedidos reales, inventario real, Azure AI Search, Azure Speech, auditoría durable, reportes financieros oficiales y operación productiva. Azure App Service es una opción condicional para publicar la demo, no un despliegue confirmado.

## Restricciones

- No almacenar credenciales en código fuente ni mostrar valores secretos.
- Usar archivos sintéticos o autorizados para probar Document Intelligence.
- No afirmar beneficios de negocio o precisión que no hayan sido medidos.
- Mantener cambios de arquitectura dentro del alcance escolar aprobado.
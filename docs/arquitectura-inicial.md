# Arquitectura inicial — Proyecto Río Claro

> Documento histórico de la propuesta inicial. Las tecnologías y beneficios
> planteados aquí no sustituyen el estado implementado que se describe al final.

Problema de Negocio
La empresa Río Claro presenta dos necesidades:

Automatizar la captura de información de facturas recibidas en PDF e imágenes.
Implementar un asistente inteligente para consultas de empleados y clientes.
Solución Propuesta
Se plantea una aplicación web basada en servicios de Azure AI que permita:

Procesar facturas automáticamente.
Extraer información estructurada.
Consultar información empresarial mediante IA generativa.
Centralizar la interacción en una única aplicación.
Componentes Iniciales
Frontend
Streamlit
Procesamiento documental
Azure AI Document Intelligence
Inteligencia Artificial
Azure AI Foundry
GPT-4.1-mini
Almacenamiento documental
Archivos empresariales
Casos de Uso
Caso de Uso 1
Captura automática de facturas:

Factura
   ↓
Document Intelligence
   ↓
Datos estructurados
Caso de Uso 2
Asistente inteligente:

Usuario
   ↓
GPT
   ↓
Respuesta
Beneficios Esperados

Estos beneficios fueron hipótesis del caso de negocio; no se han medido en un
proceso operativo ni deben presentarse como resultados demostrados.

Reducción de captura manual.
Menor cantidad de errores.
Acceso rápido a información empresarial.
Mejor experiencia de usuario.

## Evolución respecto de la propuesta

La demostración actual usa Azure AI Foundry con el modelo definido por
`FOUNDRY_MODEL`, documentos locales de muestra separados por audiencia y rol,
Azure Speech para chat de voz, y Microsoft Entra ID para la experiencia de
personal. El catálogo, el inventario y los pedidos son datos sintéticos o
demostrativos. La aplicación está publicada en Azure App Service Linux Basic
B1 en West US; no es un sistema productivo. Los resultados y pendientes
verificados se resumen en [avance-proyecto.md](./avance-proyecto.md).
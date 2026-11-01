# Plan de trabajo — Proyecto escolar Río Claro

## Propósito

Este plan guía al constructor para completar una demostración escolar funcional y coherente con el repositorio actual. **No describe un sistema empresarial de producción ni presupone que existan datos, sistemas o recursos que el equipo no tiene.**

La prioridad es demostrar los flujos principales, dejar claros sus límites y validar el funcionamiento con pruebas locales y servicios Azure ya configurados. No ampliar el alcance hacia una plataforma productiva sin aprobación explícita.

## Alcance aprobado

| Componente | Alcance del proyecto |
|---|---|
| Aplicación | Interfaz Streamlit ejecutable localmente y publicada para la demostración escolar en Azure App Service Linux con plan Basic B1; no es un sistema productivo. |
| Página principal | Mostrar el mensaje exacto «Bienvenidos a la página de Rio Claro» y dos opciones claras: clientes y personal/empleados de Río Claro. |
| Experiencia de clientes | Permitir acceso al catálogo y asistente de texto/voz sin iniciar sesión. «Estado del pedido» usa acceso genérico simulado sin verificación de identidad y consulta solo pedidos sintéticos. |
| Experiencia de empleados | Conservar el acceso protegido por Microsoft Entra ID y roles, junto con el asistente interno existente y sus permisos documentales. La demostración se valida con la cuenta administradora disponible; se omiten pruebas separadas de `obrero` y `finanzas` porque no habrá cuentas para ello. |
| Asistentes | Conservar la integración real con Azure AI Foundry y el modelo configurado. El asistente de clientes solo puede usar información aprobada para clientes; el asistente interno conserva las restricciones por rol. Ambos ofrecerán chat de voz bidireccional: transcripción de audio a texto y lectura hablada de la respuesta. |
| Voz | Integrar captura/transcripción y síntesis de voz con los asistentes existentes, sin crear agentes separados ni saltarse los controles de acceso. Se reutiliza el recurso Azure Speech F0 existente; no aprovisionar recursos adicionales ni incurrir en costos no autorizados. No conservar grabaciones de audio. |
| Conocimiento | Usar los archivos de texto de `data/` como contenido demostrativo. El flujo pasa al modelo los documentos autorizados por rol y muestra referencias a los archivos que el modelo cita, restringidas a los documentos enviados; no requiere Azure AI Search ni una base vectorial. |
| Facturas | Permitir que finanzas/administración carguen un archivo de ejemplo o autorizado durante la demostración y conservar la integración real con Azure AI Document Intelligence. No se cuenta con un conjunto de facturas empresariales ni se deben inventar datos reales. |
| Catálogo e inventario | Mantener los archivos locales de juguete como fuente de solo lectura. Sirven para demostrar búsqueda y filtros, no representan existencias ni precios operativos. |
| Pedidos | «Estado del pedido» usa acceso simulado sin verificación de identidad y consulta únicamente datos sintéticos identificados como ficticios. El número de pedido debe coincidir con el nombre de cliente. No hay conexión a pedidos reales. El asistente también puede consultar el pedido si recibe ambos datos. |
| Estados de facturas | Proveedor, RFC de proveedor/cliente, cliente, folio, subtotal, total e IVA requieren confirmación si su confianza es menor a 80% o no está disponible. Después, las facturas confirmadas como vigentes pueden guardarse explícitamente en SQLite local de demostración, sin archivo fuente ni carácter de auditoría o reporte oficial. |
| Identidad | Conservar Microsoft Entra ID y autorización por roles para personal. El acceso genérico a pedidos es una simulación sin autenticación y solo se permite para ejemplos sintéticos. |
| Publicación | Continuar con Azure App Service Linux en plan Basic B1. El aprovisionamiento Free F1 no fue posible; el costo estimado de B1 es USD 0.018/h (aprox. USD 13.14 por 730 horas), sin incluir telemetría ni otros servicios. No cambiar SKU ni aprovisionar servicios adicionales sin autorización. |

### Fuera de alcance

No construir ni simular como si fueran reales:

- Bases de datos empresariales, almacenamiento de documentos persistente, colas, auditoría durable o retención empresarial. Se permite una SQLite local aislada para la demostración aprobada de facturas.
- ERP, fuentes operativas de inventario, catálogo real o servicios de pedidos. Los ejemplos sintéticos no se conectan a fuentes reales.
- Reportes presentados como ventas oficiales.
- Azure AI Search, almacenamiento de documentos en Azure o búsqueda vectorial.
- Administración real de usuarios o funciones administrativas operativas; las cuentas Entra de prueba solo sirven para validar roles.
- Persistencia de audio, uso productivo de voz o costos de servicios adicionales sin autorización.
- Flujos de producción, monitoreo empresarial, acuerdos de disponibilidad o recuperación ante desastres.

Una mejora fuera de alcance solo se agrega con aprobación del responsable del proyecto. No se deben crear recursos Azure ni consumir servicios adicionales por anticipado.

## Estado actual observado

- **Implementado:** aplicación Streamlit; carga de PDF/JPG/JPEG/PNG y llamada a `prebuilt-invoice`; chat con Foundry; lectura de conocimiento local por rol; catálogo e inventario de archivos locales; autenticación y controles de rol en código.
- **Demostrativo:** pedidos sintéticos consultados con nombre y número; guardado opcional de campos de factura revisados en SQLite local; controles de actualización del inventario y administración.
- **Alcance acordado:** se omiten las pruebas separadas para `obrero` y `finanzas` porque no habrá cuentas Entra para ello; esto no significa que esos roles hayan sido validados. La voz no debe almacenar audio.
- **Implementado y validado manualmente por el usuario:** chat de voz de clientes y empleados con Azure Speech: transcripción en español al asistente existente, lectura de respuestas, envío automático al detener la grabación, reproducción automática intentada con reproductor de respaldo, audio de entrada no guardado y continuidad por texto. El usuario confirmó que el chat de voz funciona correctamente en ambas experiencias. El recurso existente `rio-claro-speech` (F0, West US) y sus App Settings están configurados.
- **Límites conocidos:** el acceso genérico no es autenticación real; la SQLite local no es un sistema empresarial ni una auditoría; los documentos se incluyen completos, sin recuperación por relevancia; las referencias muestran nombres de archivos indicados por el modelo, no fragmentos comprobados; los archivos de catálogo e inventario son datos de juguete.
- **Pruebas:** la suite unitaria pasa con el entorno virtual del proyecto y servicios simulados. Esto no sustituye la validación manual de las credenciales ni de las llamadas reales a Azure.
- **Configuración revisada:** el archivo `.env` ya no presenta errores de formato y contiene las variables requeridas. No registrar ni mostrar sus valores durante verificaciones posteriores.

El constructor debe confirmar el código antes de modificarlo y no volver a implementar módulos que ya existen.

## Plan de ejecución

### Fase 1 — Alinear configuración y documentación

- Verificar que las variables requeridas de `.env` se cargan sin imprimir sus valores.
- Conservar las versiones fijadas en `requirements.txt` y las instrucciones de entorno virtual.
- Alinear README, arquitectura y guion de presentación con este alcance: datos sintéticos, acceso de pedidos simulado, revisión humana y SQLite local de facturas, y servicios Azure que sí se usan.
- Mantener `.env` y `.streamlit/secrets.toml` fuera del control de versiones.

**Aceptación:** la configuración local se carga sin advertencias de formato; las instrucciones permiten arrancar la app y ejecutar las pruebas sin credenciales de Azure en las pruebas unitarias.

### Fase 2 — Verificar identidad y permisos para la demo

- Conservar el inicio de sesión Entra ID configurado para Streamlit; documentar los valores de configuración como nombres, nunca como secretos.
- Verificar que la redirección local y los claims de tenant, usuario y rol coinciden con la configuración de la aplicación Entra.
- Mantener la autorización en servicios además de ocultar módulos en la interfaz.
- Mantener protegida la experiencia de empleados con Entra ID y roles. El catálogo y el asistente de clientes serán accesibles sin iniciar sesión.
- La validación de la demostración se limita a la cuenta administradora disponible. Por decisión del usuario, no solicitar ni crear cuentas separadas para `obrero` o `finanzas`; no afirmar que sus permisos se hayan probado.
- Etiquetar el acceso genérico a pedidos como simulado, no seguro y limitado a datos sintéticos; no reutilizarlo para pedidos reales.
- Mantener en el código la autorización por rol para módulos y documentos, aunque no se realicen pruebas manuales de `obrero` y `finanzas`.
- Mantener claro que el acceso genérico a pedidos no verifica identidad y nunca debe usarse con datos reales.

**Aceptación:** la cuenta administradora disponible accede a la experiencia protegida; se documenta explícitamente que no se prueban los roles `obrero` y `finanzas` por decisión de alcance y falta de cuentas; catálogo y asistente de clientes están disponibles públicamente; el acceso simulado a pedidos indica que no verifica identidad y solo devuelve datos sintéticos.

### Fase 3 — Cerrar los flujos demostrativos existentes

- **Página principal y navegación:** mostrar «Bienvenidos a la página de Rio Claro» y dos opciones diferenciadas para clientes y personal/empleados. La opción de clientes conduce al catálogo y al asistente; la opción de empleados conserva la protección por Entra ID y roles.
- **Facturas:** probar un archivo sintético, de muestra o autorizado por el equipo contra Document Intelligence; mostrar campos reconocidos y los mensajes de error esperados. No persistir el archivo fuente.
- Revisar solo proveedor, RFC de proveedor/cliente, cliente, folio, subtotal, total e IVA cuando su confianza sea menor a 80% o no esté disponible. Permitir guardar campos y confianzas con acción explícita en la SQLite local; no presentarla como auditoría ni reporte financiero.
- **Catálogo e inventario:** preservar lectura, búsqueda y filtros sobre los archivos locales. Identificar los datos como demostrativos y no ofrecer una actualización que implique modificar un sistema real.
- **Estado del pedido:** permitir acceso de demostración por nombre y consultar solo el conjunto local sintético. No presentar el acceso como verificación de identidad ni los estados como pedidos reales.

**Aceptación:** cada módulo indica con claridad si consulta un servicio real, un archivo demostrativo o una simulación; las fallas no se presentan como éxitos.

### Fase 4 — Validar el asistente y el conocimiento

- Conservar la llamada real a Azure AI Foundry y el historial de conversación limitado a la sesión.
- Ofrecer un asistente en la experiencia de clientes y otro en la de empleados. El asistente de empleados conserva la lógica y los permisos por rol existentes; el de clientes solo recibe contenido aprobado para clientes y nunca documentos internos.
- Usar los documentos locales pequeños como contexto; no integrar Azure AI Search ni crear índices.
- Revisar el asistente de clientes con preguntas de catálogo, horarios y políticas públicas, y el de empleados con preguntas acordes a sus roles. Ambos deben reconocer cuando los documentos no respaldan una respuesta y no afirmar que el contenido demuestra datos operativos reales.
- Mostrar referencias a los nombres de archivo que el modelo identifique como respaldo, restringidas a los documentos enviados y sin presentarlas como citas literales o búsqueda empresarial avanzada.
- **Chat de voz:** clientes y empleados transcriben audio al asistente Foundry existente correspondiente y pueden escuchar sus respuestas. El usuario confirmó que el flujo base de clientes funciona. La versión actual envía la grabación al detenerla e intenta reproducir la respuesta automáticamente; esa mejora y el flujo de empleados aún deben probarse. La voz no cambia los permisos, el contexto documental ni la identidad de cada experiencia.
- La integración usa `AZURE_SPEECH_KEY` y `AZURE_SPEECH_REGION`, documentadas en README. Se reutiliza el recurso existente `rio-claro-speech` (F0, West US); no se aprovisionó otro recurso. Antes de una llamada real, confirmar el uso/cuota esperados y la autorización del usuario; la aprobación de B1 no autoriza cargos adicionales.
- No guardar grabaciones. Informar al usuario cuando el audio se envía al servicio de voz; permitir continuar por texto si el micrófono o el servicio no está disponible.

**Aceptación:** ambos asistentes responden en español por texto y voz cuando los servicios están disponibles; la transcripción entra al asistente correcto; las respuestas respetan los permisos por audiencia/rol; errores de micrófono, Speech y Foundry se muestran claramente; las pruebas unitarias no requieren credenciales ni llamadas reales; las pruebas manuales confirman ambos flujos y que no se persiste audio.

### Fase 5 — Pruebas y preparación de la presentación

- Ejecutar `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.
- Mantener los servicios de Azure simulados en pruebas unitarias; no exigir claves ni llamadas externas para correrlas.
- Realizar una comprobación manual de la app con la configuración disponible: bienvenida y navegación principal, acceso de clientes al catálogo y al asistente, acceso simulado y pedidos sintéticos, roles de empleados, revisión/guardado de factura de muestra y chat.
- **Validado manualmente por el usuario (31-10-2026):** acceso con usuario genérico, botón «Confirmo que los datos son correctos» y botón «Guardar datos».
- **Validado manualmente por el usuario (31-10-2026):** consulta de pedido sintético, filtro del catálogo y acceso con usuarios definidos en `pedidos_demo.json`.
- **Validado manualmente por el usuario (31-10-2026):** navegación de Inicio al resto de experiencias y regreso a Inicio; botones «Guardar datos» y «Guardar datos extraídos en la base de demostración».
- **Validado manualmente por el usuario (31-10-2026):** asistentes de clientes y personal respondieron correctamente preguntas de catálogo y políticas, con referencias y permisos del perfil disponible.
- **Validado manualmente en la interfaz local (31-10-2026):** preguntar por estado de pedidos sin datos pide número y nombre sintéticos; con `RC-DEMO-1001` y «Ana López» devuelve el estado de muestra y referencia `pedidos_demo.json`. Las preguntas de pedidos se interceptan antes de Foundry.
- **Validado manualmente por el usuario (31-10-2026):** pulsar Enter en los campos de revisión de factura ya no envía el formulario ni guarda automáticamente todos los campos pendientes de confirmación.
- **Validado manualmente por el usuario (31-10-2026):** la revisión de confianza baja mostró el aviso y permitió editar, guardar y confirmar los datos. No se compartieron datos de la factura.
- **Alcance de identidad acordado con el usuario (31-10-2026):** la demostración usa la cuenta administradora disponible. Se omiten por decisión del usuario las pruebas separadas de `obrero` y `finanzas`; no se afirma que esos roles hayan sido validados.
- **Validación manual del chat de voz (31-10-2026):** el usuario confirmó que el chat de voz de clientes y empleados funciona correctamente con el envío automático al detener la grabación y el intento de reproducción automática de la respuesta. No se reportaron problemas; las grabaciones no se persisten. Se reutiliza `rio-claro-speech` F0 existente; no se aprovisionó un recurso adicional.
- **Verificación del desplegador (01-11-2026 UTC):** el ZIP de 20 archivos terminó con `RuntimeSuccessful`; el App Service está `Running` y la URL pública y `/_stcore/health` respondieron HTTP 200. La sesión de navegador nueva muestra el texto de envío/reproducción automáticos y el control Record, sin botón de envío manual ni aviso de Speech no configurado. No se modificaron App Settings ni recursos. Se rotaron las claves activas de Foundry y Document Intelligence y el secreto de firma OIDC, con verificación HTTP 200.
- El informe y el código son las evidencias documentales y técnicas del
  proyecto. El usuario prepara el PPT por separado y tomará allí las capturas
  de la aplicación; estas no son entregables pendientes de este repositorio.
  El equipo está compuesto por el usuario responsable del proyecto y el
  asistente de IA como apoyo técnico y documental.
  No declarar pruebas reales de Azure o despliegue si no se ejecutaron.

**Aceptación:** pruebas unitarias aprobadas; pasos de demo reproducibles; limitaciones y cualquier dependencia de credenciales explicadas.

### Fase 6 — Publicación escolar sencilla (condicional)

Esta fase se transfiere al desplegador con las decisiones y límites siguientes:

- **Destino autorizado:** Azure App Service para Linux, en `westus`, dentro del grupo existente `rg-rio-claro-ai901` y la suscripción Azure for Students. No recrear el grupo ni cambiar de suscripción o región sin aprobación.
- **Plan y costo:** se confirma continuar con Basic B1 Linux en West US porque Free F1 no pudo aprovisionarse. El costo estimado de B1 es USD 0.018/h (aprox. USD 13.14 por 730 horas). Mantener este SKU salvo nueva autorización. Esta aprobación no autoriza costos adicionales de Speech, telemetría u otros servicios.
- **Recursos existentes:** comprobar disponibilidad regional y estado del plan antes de crear recursos. La consulta de cuota no informó límite para `Microsoft.Web/sites` ni `Microsoft.Web/serverfarms`, pero la consulta de disponibilidad regional falló; no interpretar el resultado de cuota como prueba de disponibilidad de F1.
- **Puerta de seguridad OIDC:** no incluir `.streamlit/secrets.toml` ni `.env` en el paquete. Antes de publicar, implementar y probar un arranque que obtenga los valores OIDC desde App Settings y escriba el archivo global `~/.streamlit/secrets.toml` en el entorno de ejecución, sin imprimir secretos. Mantener la autenticación y autorización por roles; no publicar una aplicación con inicio de sesión interno roto. El secreto local de firma OIDC ya fue rotado y no se debe restaurar el valor anterior.
- **Microsoft Entra ID:** después de obtener el hostname HTTPS, registrar `https://<app-name>.azurewebsites.net/oauth2callback` como redirect URI y comprobar el flujo de inicio de sesión con la cuenta administradora disponible. Por decisión del usuario, no crear cuentas separadas ni ejecutar pruebas para los roles `obrero` y `finanzas`; no declarar esos roles como verificados.
- **Identidad y telemetría:** la guía de despliegue de App Service solicita identidad administrada, Application Insights y diagnósticos. No crear recursos nuevos. El usuario autorizó reutilizar los recursos existentes de Application Insights/Log Analytics y aceptó posibles cargos variables de ingesta; el costo dependerá del volumen real de telemetría y no se puede fijar antes de operar la demo. No omitir esta advertencia ni ampliar el alcance.
- **Validación antes de aprovisionar:** usar Bicep en `infra/` y ejecutar `az deployment group what-if` contra el grupo existente. Revisar el resultado con el usuario antes de aplicar cambios. No aprovisionar si el plan intenta crear recursos fuera del alcance, si el costo excede el límite autorizado o si la disponibilidad/cuota no está confirmada.
- **Publicación y verificación:** excluir `.env`, `.streamlit/secrets.toml`, `.demo-data/` y cualquier dato local sensible del paquete. Configurar las variables requeridas por `app/config.py` en App Settings sin exponer sus valores. Tras publicar, comprobar la URL HTTPS, la navegación pública, Foundry, Document Intelligence con datos sintéticos o autorizados y el inicio de sesión de la cuenta administradora; registrar los fallos sin presentarlos como éxitos.
- **Límites de alcance:** no crear ni integrar Azure AI Search, Storage, bases de datos empresariales, pedidos reales u otros servicios no aprobados. Se reutiliza el recurso Speech F0 existente; cualquier recurso adicional o uso que pueda generar cargos requiere estimación y autorización. No reutilizar el grupo para borrar o modificar recursos ajenos a esta aplicación.
- **Entregables del desplegador:** mantener `infra/deployment.md`, `infra/azure-resources.md` e `infra/rollback.md` actualizados con el estado real. Si la fase se detiene, indicar los bloqueos y confirmar que no se crearon recursos; si se completa, incluir recursos/SKU/región, costo estimado, URL comprobada, pruebas realizadas y procedimiento para retirar únicamente los recursos nuevos.

**Aceptación:** la fase no se considera completa hasta superar las puertas de disponibilidad, costo, OIDC, telemetría autorizada, `what-if` y las verificaciones posteriores a la publicación. Si una puerta falla antes de aprovisionar, detenerse; si el bloqueo se detecta después, documentarlo y no declarar el flujo afectado listo para usuarios. La autorización del plan F1/B1 no autoriza cargos de telemetría ni otros recursos adicionales.

### Fase 7 — Instrucciones y cierre del documentador

Entregar al documentador el estado aprobado, las evidencias disponibles y las siguientes tareas:

- Revisar `README.md`, `docs/arquitectura-inicial.md`, `docs/arquitectura-detallada.md`, `docs/arquitectura-final.md`, `docs/proyecto-final.md`, `docs/guion-presentacion.md` y `docs/responsible-ai.md` para alinear la descripción con el App Service B1 desplegado y el chat de voz bidireccional ya validado por el usuario. Indicar que las pruebas separadas de `obrero` y `finanzas` se omiten por decisión del usuario y no se reportan como realizadas.
- Alinear `docs/backlog.md` y este plan con el alcance aprobado. Indicar que se reutiliza el recurso Speech F0 existente y que no deben incurrirse costos adicionales sin autorización.
- Mantener `infra/deployment.md`, `infra/azure-resources.md` e `infra/rollback.md` de acuerdo con evidencia verificable; registrar como omitidas por decisión del usuario las pruebas separadas de `obrero` y `finanzas`, sin presentarlas como bloqueos pendientes ni como roles validados.
- Mantener los pasos de demostración documentados. El informe y el código son
  las evidencias del proyecto; las capturas se preparan en el PPT externo que
  el usuario está elaborando. No registrarlas como pendientes de este
  repositorio. El usuario y el asistente de IA se reconocen como equipo de
  trabajo, con funciones diferenciadas.
- Conservar explícitamente la zona horaria de las verificaciones: los registros de Azure del 01-11-2026 están en UTC y el reloj local de esta sesión marca 31-10-2026 (UTC-6). No presentar esos timestamps como fechas locales verificadas ni afirmar estados sin evidencia.

**Aceptación:** la documentación es coherente con el alcance aprobado, diferencia hechos verificados de pruebas omitidas o no realizadas y señala materiales de presentación que requieran información del equipo; no inventa datos para eliminar marcadores legítimamente pendientes.

**Cierre documental:** informe consolidado en `docs/avance-proyecto.md`; diario,
README, arquitectura, presentación, Responsible AI, backlog y documentación de
despliegue alineados con el estado verificado. El PPT y sus capturas se preparan
fuera del repositorio por el usuario.

### Estado de ejecución (01-11-2026 UTC)

- El primer aprovisionamiento F1 falló con `QuotaExceeded` y errores de arranque. El usuario revisó y aprobó el `what-if` de B1 antes de aplicarlo.
- El App Service B1 está en `westus` y `Running`. La tarifa es USD 0.018/h, aproximadamente USD 13.14/mes a 730 horas, sin incluir telemetría, impuestos ni consumo de otros servicios.
- La URL HTTPS `https://azapplh7c7u3mxydas.azurewebsites.net/` devolvió HTTP 200 con TLS válido. Se cargaron la página de inicio y la experiencia pública «Catálogo y asistente de clientes».
- El callback Entra `https://azapplh7c7u3mxydas.azurewebsites.net/oauth2callback` está registrado y se conservó el callback local existente. El primer intento de inicio falló porque el despliegue no instaló Authlib; se corrigió `requirements.txt` a `streamlit[auth]==1.66.1` y se publicó nuevamente. **Validado manualmente por el usuario (31-10-2026):** inicio de sesión Entra exitoso; al regresar a la página principal hay que elegir de nuevo «Personal / empleados» para entrar al área autenticada. Se muestran las opciones de administración, facturas y asistente, consistente con el rol administrador. No se compartieron credenciales.
- El despliegue OneDeploy terminó con éxito y Oryx informó cero errores y advertencias. Pasaron las 60 pruebas unitarias y se validaron Bicep, los parámetros JSON, PowerShell y el arranque.
- Una consulta real al asistente público de Foundry respondió una pregunta sintética sobre horarios y citó `horarios.txt`.
- **Validado manualmente por el usuario (31-10-2026):** en la interfaz desplegada, el usuario cargó y analizó una factura; confirmó los datos extraídos y los guardó en la base local de demostración.
- **Validado manualmente por el usuario (31-10-2026):** el asistente de empleados funcionó con la sesión autenticada y los botones de administración mostraron los mensajes definidos.
- Una llamada real adicional a Document Intelligence, mediante `analizar_factura()` y un PDF sintético en memoria, también extrajo folio, proveedor, cliente, subtotal, impuesto y total.
- **Mejora de navegación (01-11-2026):** por solicitud del usuario, una sesión autenticada nueva ahora inicia en «Personal / empleados» para evitar elegir la experiencia por segunda vez tras el callback. El usuario confirmó que el comportamiento quedó corregido.
- **Estado de aceptación:** publicación, inicio de sesión de administrador, navegación automática a Personal, flujo de facturas, voz e integraciones probadas para el alcance escolar. El usuario confirmó que cerró sesión varias veces y volvió a autenticarse para acceder a la información protegida. Las pruebas separadas de `obrero` y `finanzas` se omiten por decisión del usuario; no son bloqueos pendientes ni se reportan como roles validados. El detalle está en `infra/deployment.md` e `infra/azure-resources.md`.

## Orden recomendado para el constructor

1. Verificar la configuración sin exponer secretos.
2. Ejecutar las pruebas existentes y conservar los comportamientos aprobados.
3. Validar Entra ID y permisos con la configuración disponible.
4. Probar manualmente los servicios reales de Foundry y Document Intelligence con datos sintéticos o autorizados.
5. Afinar etiquetas de demostración, errores y documentación de los módulos.
6. Preparar el despliegue escolar únicamente si se confirma que se necesita y que hay recursos disponibles.

No bloquear la demostración por carecer de una base empresarial, pedidos reales, inventario real o facturas empresariales: esos elementos están expresamente fuera del alcance.

## Riesgos y controles apropiados al proyecto

| Riesgo | Control |
|---|---|
| Confundir archivos de juguete con datos de negocio | Etiquetarlos como demostrativos en la interfaz y presentación. |
| Exponer información interna al asistente de clientes | Separar el contexto de clientes del conocimiento interno y probar que no reciba documentos restringidos por rol. |
| Confundir acceso simulado con autenticación o con pedidos reales | Avisar que el nombre no verifica identidad y mostrar solo el conjunto de pedidos sintéticos. |
| Subir una factura con información personal o fiscal a Azure | Usar archivos sintéticos o autorizados; no incluir documentos reales en el repositorio ni en capturas. |
| Confundir la SQLite local con una base empresarial | Etiquetarla como demo, guardar solo bajo acción explícita y no presentarla como auditoría o reporte oficial. |
| Respuesta del chat sin respaldo | Limitar el contexto a los archivos aprobados por rol y pedir validación cuando falte información. |
| Credenciales ausentes o incorrectas | Mostrar nombres de variables faltantes, nunca sus valores; explicar qué servicio requiere configuración. |
| Costos o indisponibilidad de servicios Azure | Hacer llamadas reales solo durante pruebas/demos necesarias y mantener mensajes de error claros. |
| Interpretar una demo como producto productivo | En documentación e interfaz, distinguir lo implementado, lo simulado y lo no conectado. |

## Componentes existentes a revisar

- `app/main.py`: pantallas, mensajes y flujos demostrativos por rol.
- `app/config.py`: configuración requerida y carga de entorno.
- `app/auth_service.py`: identidad y autorización.
- `app/document_service.py` y `app/invoice_policy.py`: extracción y estados temporales de facturas.
- `app/chat_service.py` y `app/rag_service.py`: Foundry y contexto local autorizado.
- `app/catalog_service.py` y `app/inventory_service.py`: lectura de archivos de juguete.
- `app/orders_service.py`: servicio de pedidos con repositorio no configurado; no conectar a un sistema inexistente.
- `tests/`: pruebas unitarias existentes.
- `README.md`, `docs/` e `infra/`: mantener documentación y plan de publicación coherentes con el alcance aprobado.

Esta lista identifica componentes ya presentes; el constructor debe reutilizarlos y evitar crear infraestructura o servicios que el alcance excluye.

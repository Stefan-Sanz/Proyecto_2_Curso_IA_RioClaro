from hashlib import sha256

import streamlit as st

from auth_service import (
    AuthenticationError,
    AuthorizationError,
    Principal,
    ROLE_ADMINISTRADOR,
    ROLE_FINANZAS,
    ROLE_OBRERO,
    crear_principal,
    crear_principal_publico,
    exigir_rol,
)
from config import AppConfig, ConfigurationError, load_config
from document_service import DocumentAnalysisError, analizar_factura
from chat_service import ChatServiceError, preguntar_rio_claro
from catalog_service import (
    CatalogDataError,
    buscar_productos,
    cargar_catalogo,
)
from inventory_service import (
    InventoryDataError,
    SUCURSALES,
    cargar_inventario,
    listar_existencias,
)
from invoice_policy import (
    STATUS_CANCELLED,
    STATUS_CURRENT,
    STATUS_DUPLICATE,
    STATUS_PENDING,
    INVOICE_CONFIDENCE_REVIEW_FIELDS,
    INVOICE_CONFIDENCE_REVIEW_THRESHOLD,
    campos_para_revision_humana,
    crear_registro_factura,
    detectar_indicios_duplicidad,
    registrar_revision_humana,
    registros_reportables,
)
from invoice_store_service import (
    InvoiceStorageError,
    guardar_factura_demo,
    listar_facturas_demo,
)
from orders_service import (
    OrderNotFoundError,
    OrdersDemoDataError,
    consultar_pedido_sintetico,
)
from speech_service import SpeechServiceError, sintetizar_voz, transcribir_audio

try:
    config = load_config()
except ConfigurationError as error:
    st.error(f"Configuración incompleta. {error}")
    st.stop()

try:
    logged_in = st.user.is_logged_in
except AttributeError:
    logged_in = False
    authentication_configured = False
else:
    authentication_configured = True

principal = None
authentication_error = None
if logged_in:
    try:
        principal = crear_principal(st.user.to_dict())
    except AuthenticationError as error:
        authentication_error = error

ETIQUETAS = {
    "VendorName": "Proveedor",
    "VendorTaxId": "RFC Proveedor",
    "VendorAddress": "Dirección Proveedor",

    "CustomerName": "Cliente",
    "CustomerTaxId": "RFC Cliente",
    "CustomerAddress": "Dirección Cliente",
    "CustomerAddressRecipient": "Destinatario",

    "InvoiceId": "Folio Factura",
    "InvoiceDate": "Fecha Factura",
    "DueDate": "Fecha Vencimiento",

    "InvoiceTotal": "Total",
    "SubTotal": "Subtotal",
    "TotalTax": "IVA",
    "TotalDiscount": "Descuento",

    "CurrencyCode": "Moneda",
    "PaymentTerm": "Condiciones de Pago"
}


def _seleccionar_experiencia(experiencia: str) -> None:
    st.session_state["rio_claro_experience"] = experiencia


def _seleccionar_categoria(categoria: str) -> None:
    st.session_state["customer_catalog_category"] = categoria


def _mostrar_chat(
    mensajes: list[dict[str, object]],
    principal_asistente: Principal,
    clave_historial: str,
    config: AppConfig,
) -> None:
    clave_audio_procesado = f"speech-processed-{clave_historial}"
    clave_error_entrada = f"speech-input-error-{clave_historial}"
    clave_audio_respuesta = f"speech-response-audio-{clave_historial}"
    clave_indice_audio = f"speech-response-audio-index-{clave_historial}"
    clave_indice_reproduccion_automatica = (
        f"speech-autoplay-index-{clave_historial}"
    )
    clave_error_sintesis = f"speech-synthesis-error-{clave_historial}"
    clave_indice_error_sintesis = f"speech-synthesis-error-index-{clave_historial}"

    for indice, mensaje in enumerate(mensajes):
        role = mensaje.get("role")
        content = mensaje.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str):
            continue
        with st.chat_message(role):
            st.markdown(content)
            fuentes = mensaje.get("sources")
            if (
                role == "assistant"
                and isinstance(fuentes, list)
                and fuentes
                and all(isinstance(fuente, str) for fuente in fuentes)
            ):
                st.caption(f"Fuentes: {', '.join(fuentes)}")
            elif role == "assistant":
                st.caption("Sin referencias documentales para esta respuesta.")
            if role == "assistant" and config.speech_configured:
                indice_audio = st.session_state.get(clave_indice_audio)
                audio_respuesta = st.session_state.get(clave_audio_respuesta)
                if indice == indice_audio and isinstance(audio_respuesta, bytes):
                    reproducir_automaticamente = (
                        st.session_state.get(clave_indice_reproduccion_automatica)
                        == indice
                    )
                    st.audio(
                        audio_respuesta,
                        format="audio/wav",
                        autoplay=reproducir_automaticamente,
                    )
                    if reproducir_automaticamente:
                        st.session_state[clave_indice_reproduccion_automatica] = None
                        st.caption(
                            "Si el navegador no inicia el audio, pulsa reproducir "
                            "en el control de audio."
                        )
                else:
                    if st.session_state.get(clave_indice_error_sintesis) == indice:
                        st.warning(
                            "La respuesta de texto está disponible, pero no se "
                            "pudo preparar el audio automáticamente. Puedes "
                            "intentarlo con «Escuchar respuesta»."
                        )
                    if st.button(
                        "Escuchar respuesta",
                        key=f"speech-response-{clave_historial}-{indice}",
                    ):
                        try:
                            with st.spinner("Generando audio…"):
                                audio_respuesta = sintetizar_voz(
                                    content,
                                    config.speech_key,
                                    config.speech_region,
                                )
                        except SpeechServiceError as error:
                            st.error(str(error))
                        else:
                            st.audio(audio_respuesta, format="audio/wav")

    if config.speech_configured:
        st.caption(
            "Al detener la grabación, se envía automáticamente a Azure Speech y "
            "la transcripción a este asistente. Después se intentará reproducir "
            "la respuesta; si el navegador lo bloquea, usa el reproductor. No se "
            "guarda la grabación en archivos ni en el historial. También puedes "
            "continuar por texto. El uso del servicio puede generar cargos."
        )
        audio = st.audio_input(
            "Graba tu pregunta",
            sample_rate=16000,
            key=f"speech-input-{clave_historial}",
        )
        if audio:
            audio_bytes = audio.getvalue()
            audio_hash = sha256(audio_bytes).hexdigest()
            if st.session_state.get(clave_audio_procesado) == audio_hash:
                error_entrada = st.session_state.get(clave_error_entrada)
                if isinstance(error_entrada, str):
                    st.error(error_entrada)
                else:
                    st.caption("Esta grabación ya fue enviada. Graba una pregunta nueva.")
            else:
                st.session_state[clave_audio_procesado] = audio_hash
                st.session_state.pop(clave_error_entrada, None)
                st.session_state.pop(clave_audio_respuesta, None)
                st.session_state.pop(clave_indice_audio, None)
                st.session_state.pop(
                    clave_indice_reproduccion_automatica,
                    None,
                )
                st.session_state.pop(clave_error_sintesis, None)
                st.session_state.pop(clave_indice_error_sintesis, None)
                try:
                    with st.spinner("Transcribiendo y consultando el asistente…"):
                        pregunta = transcribir_audio(
                            audio_bytes,
                            config.speech_key,
                            config.speech_region,
                        )
                        respuesta = preguntar_rio_claro(
                            pregunta,
                            principal_asistente,
                            mensajes,
                        )
                except (ChatServiceError, SpeechServiceError) as error:
                    error_entrada = (
                        f"{error} Graba una pregunta nueva para volver a intentar."
                    )
                    st.session_state[clave_error_entrada] = error_entrada
                    st.error(error_entrada)
                else:
                    mensajes.extend(
                        [
                            {"role": "user", "content": pregunta},
                            {
                                "role": "assistant",
                                "content": respuesta.answer,
                                "sources": list(respuesta.sources),
                            },
                        ]
                    )
                    indice_respuesta = len(mensajes) - 1
                    try:
                        with st.spinner("Preparando la respuesta de voz…"):
                            audio_respuesta = sintetizar_voz(
                                respuesta.answer,
                                config.speech_key,
                                config.speech_region,
                            )
                    except SpeechServiceError as error:
                        st.session_state[clave_error_sintesis] = str(error)
                        st.session_state[clave_indice_error_sintesis] = (
                            indice_respuesta
                        )
                    else:
                        st.session_state[clave_audio_respuesta] = audio_respuesta
                        st.session_state[clave_indice_audio] = indice_respuesta
                        st.session_state[clave_indice_reproduccion_automatica] = (
                            indice_respuesta
                        )
                    st.rerun()
    else:
        st.info(
            "Chat de voz no configurado. Define AZURE_SPEECH_KEY y "
            "AZURE_SPEECH_REGION para habilitarlo; puedes continuar por texto."
        )

    pregunta = st.chat_input(
        "Escribe tu pregunta",
        key=f"chat-input-{clave_historial}",
    )
    if pregunta:
        try:
            with st.spinner("Preparando una respuesta…"):
                respuesta = preguntar_rio_claro(
                    pregunta,
                    principal_asistente,
                    mensajes,
                )
        except ChatServiceError as error:
            st.error(str(error))
        else:
            mensajes.extend(
                [
                    {"role": "user", "content": pregunta},
                    {
                        "role": "assistant",
                        "content": respuesta.answer,
                        "sources": list(respuesta.sources),
                    },
                ]
            )
            st.rerun()

    if mensajes and st.button(
        "Limpiar conversación",
        key=f"clear-{clave_historial}",
    ):
        st.session_state[clave_historial] = []
        st.rerun()


if principal and principal.email:
    st.sidebar.caption(f"Sesión: {principal.email}")
if logged_in:
    st.sidebar.button("Cerrar sesión", on_click=st.logout)

st.session_state.setdefault(
    "rio_claro_experience",
    "Personal / empleados" if logged_in else "Inicio",
)
experiencia = st.sidebar.radio(
    "Experiencia",
    ["Inicio", "Clientes", "Personal / empleados"],
    key="rio_claro_experience",
)

if experiencia == "Inicio":
    st.title("Bienvenidos a la página de Rio Claro")
    st.divider()
    st.write("Selecciona la experiencia que deseas consultar.")
    st.divider()
    columna_clientes, columna_empleados = st.columns(2, gap="large")
    with columna_clientes:
        with st.container(border=True):
            st.subheader("Clientes")
            st.write("Consulta el catálogo y pregunta al asistente sin iniciar sesión.")
            st.write("")
            st.button(
                "Entrar como cliente",
                on_click=_seleccionar_experiencia,
                args=("Clientes",),
                key="enter-customer-experience",
                type="primary",
                use_container_width=True,
            )
    with columna_empleados:
        with st.container(border=True):
            st.subheader("Personal / empleados")
            st.write("Accede a las funciones internas con Microsoft Entra ID y tu rol.")
            st.write("")
            st.button(
                "Entrar como personal / empleado",
                on_click=_seleccionar_experiencia,
                args=("Personal / empleados",),
                key="enter-employee-experience",
                type="primary",
                use_container_width=True,
            )
    st.stop()

principal_publico = crear_principal_publico()
if experiencia == "Clientes":
    principal_asistente = principal_publico
    opciones = [
        "Catálogo y asistente",
        "Estado del pedido",
    ]
    modo = st.sidebar.radio(
        "Seleccione un módulo",
        opciones,
        key="customer-module",
    )
else:
    if principal is None:
        if authentication_error:
            st.error(str(authentication_error))
            st.button("Cerrar sesión", on_click=st.logout)
        else:
            st.info("Inicia sesión con Microsoft Entra ID para acceder al personal.")
            if authentication_configured:
                st.button("Iniciar sesión con Microsoft", on_click=st.login)
            else:
                st.warning(
                    "La autenticación aún no está configurada. "
                    "Consulta la sección «Acceso de usuarios» del README."
                )
        st.stop()

    roles_internos = {ROLE_OBRERO, ROLE_FINANZAS, ROLE_ADMINISTRADOR}
    if not principal.roles.intersection(roles_internos):
        st.error("La cuenta autenticada no tiene un rol interno de Río Claro asignado.")
        st.stop()

    principal_asistente = principal
    opciones = ["Asistente Interno"]
    if ROLE_OBRERO in principal.roles:
        opciones.insert(0, "Inventario por Sucursal")
    if principal.roles.intersection({ROLE_FINANZAS, ROLE_ADMINISTRADOR}):
        opciones.insert(0, "Procesamiento de Facturas")
    if ROLE_ADMINISTRADOR in principal.roles:
        opciones.insert(0, "Administración")
    modo = st.sidebar.radio(
        "Seleccione un módulo",
        opciones,
        key="employee-module",
    )

# ==========================
# MÓDULO FACTURAS
# ==========================

if modo == "Procesamiento de Facturas":
    try:
        exigir_rol(principal, {ROLE_FINANZAS, ROLE_ADMINISTRADOR})
    except AuthorizationError as error:
        st.error(str(error))
        st.stop()

    st.title("Proyecto Río Claro")

    st.markdown("### Captura inteligente de facturas")
    st.caption(
        "Carga una factura emitida en PDF o imagen para consultar sus datos extraídos."
    )

    archivo = st.file_uploader(
        "Seleccione una factura PDF o una imagen",
        type=["pdf", "jpg", "jpeg", "png"]
    )

    if archivo:
        extension = archivo.name.rsplit(".", 1)[-1].upper() if "." in archivo.name else "Archivo"
        st.caption(f"Archivo: **{archivo.name}** · {extension} · {archivo.size:,} bytes")

        if st.button("Analizar", key="analyze-invoice"):
            document = archivo.getvalue()
            try:
                with st.spinner("Analizando la factura…"):
                    analisis = analizar_factura(document, principal)
            except DocumentAnalysisError as error:
                st.error(str(error))
                st.stop()
            except AuthorizationError as error:
                st.error(str(error))
                st.stop()

            registros = st.session_state.setdefault("invoice_records", [])
            registro = crear_registro_factura(
                archivo.name,
                document,
                analisis.fields,
                analisis.confidences,
            )
            registros.append(registro)
            st.session_state["selected_invoice_id"] = registro["id"]
            st.rerun()

    st.info(
        "Los archivos y la revisión permanecen en la sesión hasta que se confirme "
        "el guardado en la base local de demostración. Usa solo documentos "
        "sintéticos o autorizados."
    )
    registros = st.session_state.setdefault("invoice_records", [])
    registro_id = st.session_state.get("selected_invoice_id")
    registro_actual = next(
        (item for item in reversed(registros) if item["id"] == registro_id),
        None,
    )

    if registro_actual:
        datos = registro_actual["fields"]
        confianzas = registro_actual.get("confidences", {})
        if not isinstance(confianzas, dict):
            confianzas = {}
        campos_revision = campos_para_revision_humana(datos, confianzas)
        campos_revisados = registro_actual.get("reviewed_fields", [])
        if not isinstance(campos_revisados, (list, tuple, set)):
            campos_revisados = []
        campos_pendientes = campos_revision - set(campos_revisados)

        st.subheader("Datos extraídos")
        st.caption(
            f"{registro_actual['filename']} · Estado: **{registro_actual['status']}**"
        )
        st.caption(
            "Proveedor, RFC del proveedor, cliente, RFC del cliente, folio, "
            "subtotal, total e IVA requieren confirmación si su confianza es menor a "
            f"{INVOICE_CONFIDENCE_REVIEW_THRESHOLD:.0%} o no está disponible. "
            "La confianza es una señal, no una garantía de exactitud."
        )
        campos_relevantes = [
            "VendorName",
            "VendorTaxId",
            "CustomerName",
            "CustomerTaxId",
            "InvoiceId",
            "InvoiceDate",
            "DueDate",
            "SubTotal",
            "TotalTax",
            "InvoiceTotal",
        ]

        def mostrar_monto(campo: str) -> str:
            valor = datos.get(campo)
            return str(valor) if valor not in (None, "") else "Sin dato"

        metrica_subtotal, metrica_impuestos, metrica_total = st.columns(3)
        metrica_subtotal.metric("Subtotal", mostrar_monto("SubTotal"))
        metrica_impuestos.metric("Impuestos", mostrar_monto("TotalTax"))
        metrica_total.metric("Total", mostrar_monto("InvoiceTotal"))

        for campo in sorted(set(datos) - set(campos_relevantes)):
            campos_relevantes.append(campo)

        with st.form(
            f"invoice-human-review-{registro_id}",
            enter_to_submit=False,
        ):
            correcciones = {}
            columnas = st.columns(2)
            for indice, campo in enumerate(campos_relevantes):
                with columnas[indice % len(columnas)]:
                    etiqueta = ETIQUETAS.get(campo, campo)
                    valor = datos.get(campo)
                    texto_valor = str(valor) if valor not in (None, "") else ""
                    confianza = confianzas.get(campo)
                    if campo in campos_pendientes:
                        correcciones[campo] = st.text_input(
                            etiqueta,
                            value=texto_valor,
                            key=f"invoice-review-{registro_id}-{campo}",
                        )
                        st.warning(
                            "Requiere confirmación: "
                            + (
                                f"{confianza:.0%} de confianza, debajo del umbral."
                                if isinstance(confianza, (int, float))
                                and not isinstance(confianza, bool)
                                else "confianza no disponible."
                            )
                        )
                    elif campo in campos_revision:
                        st.markdown(f"**{etiqueta}**")
                        st.write(texto_valor or "Sin dato")
                        st.caption("Revisión humana registrada.")
                    else:
                        st.markdown(f"**{etiqueta}**")
                        st.write(texto_valor or "Sin dato")
                        if (
                            campo in INVOICE_CONFIDENCE_REVIEW_FIELDS
                            and isinstance(confianza, (int, float))
                            and not isinstance(confianza, bool)
                        ):
                            st.caption(f"Confianza: {confianza:.0%}")
            columna_guardar, columna_confirmar = st.columns(2)
            guardar_datos = columna_guardar.form_submit_button(
                "Guardar datos",
                disabled=not campos_pendientes,
                use_container_width=True,
            )
            confirmar_datos = columna_confirmar.form_submit_button(
                "Confirmo que los datos son correctos",
                disabled=(
                    registro_actual["status"] != STATUS_PENDING or not bool(datos)
                ),
                use_container_width=True,
            )

        if guardar_datos:
            registrar_revision_humana(registro_actual, correcciones)
            st.success("Datos guardados en esta sesión.")
            st.rerun()

        if campos_pendientes:
            st.warning(
                "Confirma solo después de revisar los campos que requieren confirmación."
            )
        elif not datos:
            st.warning(
                "No se extrajeron campos. No se puede confirmar ni guardar esta factura."
            )

        indicios = detectar_indicios_duplicidad(registro_actual, registros)
        if indicios:
            st.warning(
                "Hay coincidencias que requieren revisión humana. "
                "El sistema no clasifica una factura como duplicada automáticamente."
            )
            for indicio in indicios:
                st.write(
                    f"**{indicio['filename']}** ({indicio['status']}): "
                    f"{', '.join(indicio['reasons'])}"
                )

        st.caption(
            "La confirmación humana aplica el estado solo en esta sesión de demostración."
        )
        if registro_actual["status"] in {STATUS_PENDING, STATUS_CURRENT}:
            columna_duplicada, columna_cancelada = st.columns(2)
            if columna_duplicada.button(
                "Confirmar duplicada",
                key=f"invoice-duplicate-{registro_id}",
            ):
                registro_actual["status"] = STATUS_DUPLICATE
                st.rerun()
            if columna_cancelada.button(
                "Confirmar cancelación",
                key=f"invoice-cancel-{registro_id}",
            ):
                registro_actual["status"] = STATUS_CANCELLED
                st.rerun()

        if confirmar_datos:
            if campos_pendientes:
                registrar_revision_humana(registro_actual, correcciones)
            registro_actual["status"] = STATUS_CURRENT
            st.success("Datos confirmados como correctos en esta sesión.")
            st.rerun()

        if registro_actual["status"] == STATUS_CURRENT:
            st.caption(
                "El siguiente botón guarda los campos y sus niveles de confianza "
                "en una base SQLite local, excluida del repositorio."
            )
            if st.button(
                "Guardar datos extraídos en la base de demostración",
                key=f"save-invoice-{registro_id}",
            ):
                try:
                    inserted = guardar_factura_demo(registro_actual)
                except InvoiceStorageError as error:
                    st.error(str(error))
                else:
                    if inserted:
                        st.success("Factura guardada en la base local de demostración.")
                    else:
                        st.info("Esta factura ya estaba guardada en la base de demostración.")

    vigentes = registros_reportables(registros)
    duplicadas = sum(item["status"] == STATUS_DUPLICATE for item in registros)
    canceladas = sum(item["status"] == STATUS_CANCELLED for item in registros)
    with st.expander("Resumen de facturas de esta sesión"):
        metrica_vigentes, metrica_duplicadas, metrica_canceladas = st.columns(3)
        metrica_vigentes.metric("Incluidas: vigentes", len(vigentes))
        metrica_duplicadas.metric("Excluidas: duplicadas", duplicadas)
        metrica_canceladas.metric("Excluidas: canceladas", canceladas)
        st.caption(
            "Duplicadas y canceladas no se incluyen en el conteo demostrativo y "
            "solo permanecen disponibles durante esta sesión."
        )
        for item in registros:
            st.write(f"{item['filename']} — {item['status']}")
    try:
        facturas_guardadas = listar_facturas_demo()
    except InvoiceStorageError as error:
        st.error(str(error))
    else:
        st.caption(
            f"Facturas guardadas localmente en la base de demostración: "
            f"{len(facturas_guardadas)}."
        )

# ==========================
# MÓDULOS DE ASISTENCIA IA
# ==========================

if modo in {"Catálogo y asistente", "Asistente Interno"}:
    es_asistente_clientes = modo == "Catálogo y asistente"
    if es_asistente_clientes:
        clave_historial = "chat_messages_clientes"
    else:
        alcance_historial = (
            f"{principal.tenant_id}:{principal.object_id}:"
            f"{','.join(sorted(principal.roles))}"
        )
        id_historial = sha256(alcance_historial.encode("utf-8")).hexdigest()[:16]
        clave_historial = f"chat_messages_interno_{id_historial}"

    st.title(
        "Catálogo y asistente de clientes"
        if es_asistente_clientes
        else "Asistente Interno Río Claro"
    )

    if es_asistente_clientes:
        st.info(
            "Explora el catálogo por categoría y pregunta sobre productos, "
            "horarios o políticas públicas."
        )
        st.caption(
            "Estás chateando con una IA. Sus respuestas pueden contener errores; "
            "verifica la información importante."
        )
    else:
        st.info(
            "Consulta los documentos autorizados para tu rol. "
            "Los archivos son de muestra y no representan datos operativos."
        )
        st.caption(
            "Estás chateando con una IA. Sus respuestas pueden contener errores; "
            "verifica la información importante."
        )

    mensajes = st.session_state.setdefault(clave_historial, [])

    if es_asistente_clientes:
        columna_catalogo, columna_chat = st.columns([1, 1.3], gap="large")
        with columna_catalogo:
            st.subheader("Catálogo general")
            st.caption(
                "Productos y precios de muestra; no representan una fuente comercial operativa."
            )
            try:
                catalogo = cargar_catalogo()
            except CatalogDataError as error:
                st.error(str(error))
                st.stop()

            categorias = sorted({product.category for product in catalogo})
            categorias_menu = ["Todas"] + categorias
            categoria_actual = st.session_state.get(
                "customer_catalog_category",
                "Todas",
            )
            if categoria_actual not in categorias_menu:
                categoria_actual = "Todas"
                st.session_state["customer_catalog_category"] = categoria_actual

            columnas_categorias = st.columns(2, gap="small")
            for indice, categoria in enumerate(categorias_menu):
                with columnas_categorias[indice % len(columnas_categorias)]:
                    st.button(
                        categoria,
                        key=f"customer-category-{indice}",
                        on_click=_seleccionar_categoria,
                        args=(categoria,),
                        type="primary" if categoria == categoria_actual else "secondary",
                        use_container_width=True,
                    )

            productos = buscar_productos(
                catalogo,
                category=None if categoria_actual == "Todas" else categoria_actual,
            )
            st.caption(f"{len(productos)} productos")
            for producto in productos:
                with st.container(border=True):
                    st.markdown(f"**{producto.name}**")
                    st.caption(f"{producto.presentation} · {producto.price}")
                    if producto.details:
                        st.write(producto.details)

        with columna_chat:
            st.subheader("Asistente de clientes")
            _mostrar_chat(mensajes, principal_asistente, clave_historial, config)
    else:
        _mostrar_chat(mensajes, principal_asistente, clave_historial, config)

if modo == "Inventario por Sucursal":
    try:
        snapshot = cargar_inventario(principal)
    except (AuthorizationError, InventoryDataError) as error:
        st.error(str(error))
        st.stop()

    st.title("Inventario por Sucursal")
    st.caption(
        f"Actualizado: {snapshot.updated_at:%d/%m/%Y}. "
        "Disponible significa 5 unidades o más. "
        "Las sucursales sin registro se muestran como «Sin dato». "
        "Datos de juguete para demostración; no representan existencias reales."
    )
    sucursal = st.selectbox("Sucursal", ["Todas"] + list(SUCURSALES))
    busqueda = st.text_input("Buscar producto")
    filas = listar_existencias(
        snapshot,
        sucursal=None if sucursal == "Todas" else sucursal,
        busqueda=busqueda,
    )
    if filas:
        cantidades_disponibles = sum(
            1
            for row in filas
            for key, value in row.items()
            if key.startswith("Disponibilidad ")
            and value == "Disponible"
        )
        productos_columna, sucursales_columna, disponibilidad_columna = st.columns(3)
        productos_columna.metric("Productos", len(filas))
        sucursales_columna.metric(
            "Sucursales consultadas",
            1 if sucursal != "Todas" else len(SUCURSALES),
        )
        disponibilidad_columna.metric(
            "Disponibilidades confirmadas",
            cantidades_disponibles,
        )
        st.dataframe(filas, use_container_width=True, hide_index=True)
    else:
        st.info("No se encontraron productos para los filtros seleccionados.")
    if st.button("Actualizar inventario", key="inventory-update"):
        st.info("En desarrollo: la actualización no modifica el archivo de inventario.")

if modo == "Estado del pedido":
    st.title("Estado del pedido")
    st.warning(
        "Acceso de demostración: escribir un nombre no verifica identidad. "
        "Esta pantalla solo consulta pedidos sintéticos y no debe usarse con datos reales."
    )
    nombre_cliente_demo = st.session_state.get("demo_customer_name")
    if not isinstance(nombre_cliente_demo, str) or not nombre_cliente_demo:
        with st.form("demo-customer-login"):
            nombre_ingresado = st.text_input("Nombre del cliente de prueba")
            acceso_demo = st.form_submit_button("Iniciar sesión de demostración")
        if acceso_demo:
            if len(nombre_ingresado.strip()) < 2:
                st.error("Escribe un nombre de al menos dos caracteres.")
            else:
                st.session_state["demo_customer_name"] = nombre_ingresado.strip()
                st.rerun()
    else:
        st.caption(f"Sesión de demostración: {nombre_cliente_demo}")
        if st.button("Cerrar sesión de demostración", key="demo-customer-logout"):
            del st.session_state["demo_customer_name"]
            st.rerun()

        with st.form("demo-order-lookup"):
            numero_pedido_demo = st.text_input("Número de pedido sintético")
            consultar_demo = st.form_submit_button("Consultar pedido de muestra")
        if consultar_demo:
            try:
                pedido_demo = consultar_pedido_sintetico(
                    numero_pedido_demo,
                    nombre_cliente_demo,
                )
            except ValueError as error:
                st.error(str(error))
            except OrderNotFoundError:
                st.error(
                    "No se encontró ese pedido sintético para el nombre proporcionado."
                )
            except OrdersDemoDataError as error:
                st.error(str(error))
            else:
                st.success(f"Pedido de demostración: {pedido_demo.status}")
                st.write(f"**Número:** {pedido_demo.order_id}")
                st.write(f"**Cliente:** {pedido_demo.customer_name}")
                st.write(f"**Productos:** {', '.join(pedido_demo.items)}")
                st.caption(
                    f"Última actualización: {pedido_demo.updated_at}. "
                    "Datos ficticios; no representan pedidos reales."
                )

if modo == "Administración":
    st.title("Administración")
    st.caption(
        "Sección para la gestión de usuarios y de documentos de política de la empresa."
    )
    columna_usuarios, columna_documentos = st.columns(2)
    if columna_usuarios.button("Gestionar usuarios"):
        st.info("En desarrollo.")
    if columna_documentos.button("Actualizar documentos"):
        st.info("En proceso de creación.")
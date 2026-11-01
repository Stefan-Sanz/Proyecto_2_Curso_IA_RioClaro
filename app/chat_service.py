import json
from dataclasses import dataclass
from typing import Sequence

from openai import APIConnectionError, APIStatusError, OpenAI, OpenAIError

from auth_service import (
    Principal,
    ROLE_ADMINISTRADOR,
    ROLE_CLIENTE,
    ROLE_FINANZAS,
    ROLE_OBRERO,
    exigir_rol,
)
from config import load_config
from orders_service import OrdersDemoDataError, buscar_pedido_sintetico_en_mensaje
from rag_service import KnowledgeSourceError, obtener_documentos


class ChatServiceError(RuntimeError):
    """Raised when the assistant cannot produce a response."""


@dataclass(frozen=True)
class ChatResponse:
    answer: str
    sources: tuple[str, ...]


def preguntar_rio_claro(
    pregunta: str,
    principal: Principal,
    historial: Sequence[dict[str, object]] = (),
) -> ChatResponse:
    exigir_rol(
        principal,
        {ROLE_CLIENTE, ROLE_OBRERO, ROLE_FINANZAS, ROLE_ADMINISTRADOR},
    )

    try:
        es_consulta_pedido, pedido = buscar_pedido_sintetico_en_mensaje(pregunta)
    except OrdersDemoDataError as error:
        raise ChatServiceError(str(error)) from error
    if es_consulta_pedido:
        if pedido is None:
            return ChatResponse(
                answer=(
                    "Puedo consultar únicamente pedidos sintéticos de demostración. "
                    "Escribe el número de pedido con formato RC-DEMO-0000 y el "
                    "nombre completo del cliente de prueba. No compartas datos de "
                    "pedidos reales."
                ),
                sources=(),
            )
        return ChatResponse(
            answer=(
                f"Pedido de demostración {pedido.order_id}: estado **{pedido.status}**. "
                f"Productos: {', '.join(pedido.items)}. "
                f"Última actualización: {pedido.updated_at}. "
                "Este registro es sintético y no representa un pedido real."
            ),
            sources=("pedidos_demo.json",),
        )

    config = load_config()

    try:
        documentos = obtener_documentos(principal)
    except KnowledgeSourceError as error:
        raise ChatServiceError(str(error)) from error

    nombres_fuentes = [documento.filename for documento in documentos]
    contenido_documentos = "".join(
        f"\n\n### {documento.filename}\n{documento.content}"
        for documento in documentos
    )

    if principal.roles.intersection(
        {ROLE_OBRERO, ROLE_FINANZAS, ROLE_ADMINISTRADOR}
    ):
        prompt_sistema = """
            Eres el asistente interno de Río Claro.
            Responde siempre en español, con lenguaje profesional y claro.
            Utiliza únicamente la información proporcionada y autorizada para el rol.
            Los archivos son demostrativos y no acreditan datos operativos reales.
            Si falta información, indícalo y pide validación al personal responsable.
            No inventes existencias, estados de pedidos ni resultados de negocio.
            En "sources", incluye solo los nombres exactos de los documentos
            que respaldan directamente la respuesta. Si ninguno la respalda,
            devuelve una lista vacía. No inventes fuentes.
            Mantén las respuestas breves y enfocadas.
            """
    else:
        prompt_sistema = """
            Eres el asistente de clientes de Río Claro.
            Responde siempre en español, con lenguaje profesional y claro.
            Utiliza únicamente la información pública proporcionada para clientes.
            No reveles ni infieras información interna, de inventario o de facturas.
            El catálogo y los documentos son demostrativos, no datos operativos.
            No inventes precios, existencias ni estados de pedidos.
            Si falta información, indícalo y pide validación al personal de Río Claro.
            En "sources", incluye solo los nombres exactos de los documentos
            que respaldan directamente la respuesta. Si ninguno la respalda,
            devuelve una lista vacía. No inventes fuentes.
            Mantén las respuestas breves y enfocadas.
            """

    try:
        client = OpenAI(
            base_url=config.foundry_project_endpoint,
            api_key=config.foundry_api_key,
        )
        conversation = [
            {
                "role": "system",
                "content": prompt_sistema,
            },
        ]
        conversation.extend(
            {"role": message["role"], "content": message["content"]}
            for message in historial[-10:]
            if message.get("role") in {"user", "assistant"}
            and isinstance(message.get("content"), str)
        )
        conversation.append(
            {
                "role": "user",
                "content": f"""
                    Información disponible:

                    {contenido_documentos}

                    Fuentes disponibles para citar:
                    {json.dumps(nombres_fuentes, ensure_ascii=False)}

                    Pregunta:

                    {pregunta}
                    """,
            }
        )
        respuesta = client.responses.create(
            model=config.foundry_model,
            input=conversation,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "rio_claro_answer",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "answer": {"type": "string"},
                            "sources": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": nombres_fuentes,
                                },
                            },
                        },
                        "required": ["answer", "sources"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                }
            },
        )
    except (APIConnectionError, APIStatusError, OpenAIError) as error:
        raise ChatServiceError(
            "No fue posible consultar Azure AI Foundry. "
            "Verifique la conexión y la configuración del servicio."
        ) from error

    try:
        contenido_respuesta = json.loads(respuesta.output_text)
    except json.JSONDecodeError as error:
        raise ChatServiceError(
            "Azure AI Foundry devolvió una respuesta en un formato no reconocido."
        ) from error

    if not isinstance(contenido_respuesta, dict):
        raise ChatServiceError(
            "Azure AI Foundry devolvió una respuesta en un formato no reconocido."
        )

    answer = contenido_respuesta.get("answer")
    sources = contenido_respuesta.get("sources")
    if not isinstance(answer, str) or not isinstance(sources, list):
        raise ChatServiceError(
            "Azure AI Foundry devolvió una respuesta incompleta."
        )

    fuentes_permitidas = set(nombres_fuentes)
    if any(
        not isinstance(source, str) or source not in fuentes_permitidas
        for source in sources
    ):
        raise ChatServiceError(
            "Azure AI Foundry devolvió una referencia a un documento no disponible."
        )
    if not answer.strip():
        raise ChatServiceError("Azure AI Foundry devolvió una respuesta vacía.")

    return ChatResponse(
        answer=answer,
        sources=tuple(dict.fromkeys(sources)),
    )
from dataclasses import dataclass
import math

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError

from auth_service import (
    Principal,
    ROLE_ADMINISTRADOR,
    ROLE_FINANZAS,
    exigir_autenticacion,
    exigir_rol,
)
from config import load_config


class DocumentAnalysisError(RuntimeError):
    """Raised when the invoice service cannot analyze a document."""


@dataclass(frozen=True)
class InvoiceAnalysis:
    fields: dict[str, str]
    confidences: dict[str, float | None]


def _valor_de_campo(campo: object) -> str:
    valor = getattr(campo, "value", None)
    if valor is not None:
        return str(valor)

    contenido = getattr(campo, "content", None)
    if isinstance(contenido, str) and contenido:
        return contenido

    moneda = getattr(campo, "value_currency", None)
    if moneda is not None:
        importe = getattr(moneda, "amount", None)
        codigo_moneda = getattr(moneda, "currency_code", None)
        if importe is not None:
            return f"{importe} {codigo_moneda}" if codigo_moneda else str(importe)

    for atributo in (
        "value_string",
        "value_date",
        "value_time",
        "value_phone_number",
        "value_number",
        "value_integer",
        "value_selection_mark",
        "value_signature",
        "value_country_region",
        "value_boolean",
    ):
        valor = getattr(campo, atributo, None)
        if valor is not None:
            return str(valor)

    return ""


def analizar_factura(documento: bytes, principal: Principal) -> InvoiceAnalysis:
    exigir_autenticacion(principal)
    exigir_rol(principal, {ROLE_FINANZAS, ROLE_ADMINISTRADOR})
    config = load_config()

    try:
        client = DocumentIntelligenceClient(
            endpoint=config.document_intelligence_endpoint,
            credential=AzureKeyCredential(config.document_intelligence_key),
        )
        poller = client.begin_analyze_document("prebuilt-invoice", documento)
        resultado = poller.result()
    except AzureError as error:
        raise DocumentAnalysisError(
            "Azure AI Document Intelligence no pudo analizar la factura. "
            "Verifique la conexión y la configuración del servicio."
        ) from error

    if not resultado.documents:
        raise DocumentAnalysisError(
            "Azure AI Document Intelligence no reconoció una factura en el documento."
        )

    factura: dict[str, str] = {}
    confianzas: dict[str, float | None] = {}
    doc = resultado.documents[0]

    for nombre, campo in doc.fields.items():
        factura[nombre] = _valor_de_campo(campo)

        confianza = getattr(campo, "confidence", None)
        confianzas[nombre] = (
            float(confianza)
            if isinstance(confianza, (int, float))
            and math.isfinite(confianza)
            and 0 <= confianza <= 1
            else None
        )

    return InvoiceAnalysis(fields=factura, confidences=confianzas)
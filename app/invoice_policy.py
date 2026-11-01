from hashlib import sha256
from typing import Mapping, Sequence
from uuid import uuid4


STATUS_PENDING = "Pendiente de validación"
STATUS_CURRENT = "Vigente"
STATUS_DUPLICATE = "Duplicada"
STATUS_CANCELLED = "Cancelada"
REPORTABLE_STATUSES = frozenset({STATUS_CURRENT})
INVOICE_CONFIDENCE_REVIEW_THRESHOLD = 0.8
INVOICE_CONFIDENCE_REVIEW_FIELDS = frozenset(
    {
        "VendorName",
        "VendorTaxId",
        "CustomerName",
        "CustomerTaxId",
        "InvoiceId",
        "SubTotal",
        "InvoiceTotal",
        "TotalTax",
    }
)

_DUPLICATE_FIELDS = (
    ("InvoiceId", "mismo folio"),
    ("VendorName", "mismo proveedor"),
    ("InvoiceDate", "misma fecha de emisión"),
    ("InvoiceTotal", "mismo importe total"),
)


def crear_registro_factura(
    filename: str,
    document: bytes,
    fields: Mapping[str, str],
    confidences: Mapping[str, float | None] | None = None,
) -> dict[str, object]:
    return {
        "id": uuid4().hex,
        "filename": filename,
        "document_hash": sha256(document).hexdigest(),
        "fields": dict(fields),
        "confidences": dict(confidences or {}),
        "reviewed_fields": [],
        "status": STATUS_PENDING,
    }


def campos_para_revision_humana(
    fields: Mapping[str, str],
    confidences: Mapping[str, float | None],
    threshold: float = INVOICE_CONFIDENCE_REVIEW_THRESHOLD,
) -> frozenset[str]:
    return frozenset(
        field
        for field in fields
        if field in INVOICE_CONFIDENCE_REVIEW_FIELDS
        and (
            not isinstance(confidences.get(field), (int, float))
            or isinstance(confidences.get(field), bool)
            or confidences[field] < threshold
        )
    )


def registrar_revision_humana(
    record: dict[str, object],
    corrections: Mapping[str, str],
) -> None:
    fields = record.get("fields")
    confidences = record.get("confidences")
    if not isinstance(fields, dict) or not isinstance(confidences, Mapping):
        raise ValueError("El registro de factura no contiene los campos esperados.")

    required_fields = campos_para_revision_humana(fields, confidences)
    if set(corrections) != required_fields:
        raise ValueError("La revisión debe incluir todos los campos pendientes.")

    fields.update(corrections)
    record["reviewed_fields"] = sorted(required_fields)


def revision_humana_completa(record: Mapping[str, object]) -> bool:
    fields = record.get("fields")
    confidences = record.get("confidences")
    reviewed_fields = record.get("reviewed_fields")
    if not isinstance(fields, Mapping) or not fields or not isinstance(confidences, Mapping):
        return False
    if not isinstance(reviewed_fields, (list, tuple, set, frozenset)):
        return False

    required_fields = campos_para_revision_humana(fields, confidences)
    return required_fields.issubset(set(reviewed_fields))


def detectar_indicios_duplicidad(
    registro: Mapping[str, object],
    historial: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    indicios: list[dict[str, object]] = []
    current_fields = registro.get("fields", {})
    if not isinstance(current_fields, Mapping):
        return indicios

    for anterior in historial:
        if anterior.get("id") == registro.get("id"):
            continue
        anterior_fields = anterior.get("fields", {})
        if not isinstance(anterior_fields, Mapping):
            continue

        razones = []
        if registro.get("document_hash") == anterior.get("document_hash"):
            razones.append("archivo repetido")
        for field, label in _DUPLICATE_FIELDS:
            current_value = current_fields.get(field)
            previous_value = anterior_fields.get(field)
            if (
                isinstance(current_value, str)
                and current_value.strip()
                and isinstance(previous_value, str)
                and current_value.strip().casefold() == previous_value.strip().casefold()
            ):
                razones.append(label)

        if razones:
            indicios.append(
                {
                    "filename": anterior.get("filename", "Factura anterior"),
                    "status": anterior.get("status", STATUS_PENDING),
                    "reasons": tuple(razones),
                }
            )

    return indicios


def registros_reportables(
    historial: Sequence[Mapping[str, object]],
) -> list[Mapping[str, object]]:
    return [
        registro
        for registro in historial
        if registro.get("status") in REPORTABLE_STATUSES
    ]

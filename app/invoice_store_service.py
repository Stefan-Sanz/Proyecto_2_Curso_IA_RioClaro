import json
from pathlib import Path
import sqlite3
from typing import Mapping

from invoice_policy import STATUS_CURRENT, revision_humana_completa


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEMO_DATABASE = PROJECT_ROOT / ".demo-data" / "facturas.sqlite3"


class InvoiceStorageError(RuntimeError):
    """Raised when demo invoice data cannot be stored or read."""


def _connect(database_path: Path) -> sqlite3.Connection:
    try:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(database_path)
    except OSError as error:
        raise InvoiceStorageError(
            "No se pudo preparar la base local de facturas de demostración."
        ) from error
    except sqlite3.Error as error:
        raise InvoiceStorageError(
            "No se pudo abrir la base local de facturas de demostración."
        ) from error


def guardar_factura_demo(
    record: Mapping[str, object],
    database_path: Path = DEMO_DATABASE,
) -> bool:
    if record.get("status") != STATUS_CURRENT:
        raise InvoiceStorageError(
            "Solo se pueden guardar facturas confirmadas como vigentes."
        )
    if not revision_humana_completa(record):
        raise InvoiceStorageError(
            "Confirma manualmente los campos relevantes de baja confianza antes de guardar."
        )

    record_id = record.get("id")
    filename = record.get("filename")
    document_hash = record.get("document_hash")
    fields = record.get("fields")
    confidences = record.get("confidences")
    if (
        not isinstance(record_id, str)
        or not isinstance(filename, str)
        or not isinstance(document_hash, str)
        or not isinstance(fields, Mapping)
        or not isinstance(confidences, Mapping)
    ):
        raise InvoiceStorageError("El registro de factura está incompleto.")

    connection = _connect(database_path)
    try:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS demo_invoices (
                    invoice_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    document_hash TEXT NOT NULL,
                    fields_json TEXT NOT NULL,
                    confidences_json TEXT NOT NULL,
                    saved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO demo_invoices (
                    invoice_id,
                    filename,
                    document_hash,
                    fields_json,
                    confidences_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    filename,
                    document_hash,
                    json.dumps(dict(fields), ensure_ascii=False),
                    json.dumps(dict(confidences), ensure_ascii=False),
                ),
            )
            return cursor.rowcount == 1
    except (sqlite3.Error, TypeError, ValueError) as error:
        raise InvoiceStorageError(
            "No se pudieron guardar los datos en la base de demostración."
        ) from error
    finally:
        connection.close()


def listar_facturas_demo(
    database_path: Path = DEMO_DATABASE,
) -> list[dict[str, str]]:
    if not database_path.exists():
        return []

    connection = _connect(database_path)
    try:
        table_exists = connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = 'demo_invoices'
            """
        ).fetchone()
        if table_exists is None:
            return []

        rows = connection.execute(
            """
            SELECT invoice_id, filename, saved_at
            FROM demo_invoices
            ORDER BY saved_at DESC, invoice_id
            """
        ).fetchall()
    except sqlite3.Error as error:
        raise InvoiceStorageError(
            "No se pudo consultar la base local de facturas de demostración."
        ) from error
    finally:
        connection.close()

    return [
        {"id": row[0], "filename": row[1], "saved_at": row[2]}
        for row in rows
    ]

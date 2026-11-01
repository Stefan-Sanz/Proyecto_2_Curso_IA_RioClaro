import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from invoice_policy import (
    STATUS_CURRENT,
    crear_registro_factura,
    registrar_revision_humana,
)
from invoice_store_service import (
    InvoiceStorageError,
    guardar_factura_demo,
    listar_facturas_demo,
)


class InvoiceStoreServiceTests(unittest.TestCase):
    def test_saves_and_lists_a_confirmed_reviewed_invoice(self):
        record = crear_registro_factura(
            "factura-sintetica.pdf",
            b"sample",
            {"VendorName": "Río Claro", "InvoiceId": "RC-001"},
            {"VendorName": 0.95, "InvoiceId": 0.7},
        )
        registrar_revision_humana(record, {"InvoiceId": "RC-001"})
        record["status"] = STATUS_CURRENT

        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "demo.sqlite3"

            self.assertTrue(guardar_factura_demo(record, database))
            self.assertFalse(guardar_factura_demo(record, database))
            saved_records = listar_facturas_demo(database)

        self.assertEqual(len(saved_records), 1)
        self.assertEqual(saved_records[0]["id"], record["id"])
        self.assertEqual(saved_records[0]["filename"], "factura-sintetica.pdf")
        self.assertTrue(saved_records[0]["saved_at"])

    def test_does_not_save_unconfirmed_invoice(self):
        record = crear_registro_factura("factura.pdf", b"pdf", {"InvoiceId": "A-1"})

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(InvoiceStorageError, "confirmadas como vigentes"):
                guardar_factura_demo(record, Path(directory) / "demo.sqlite3")

    def test_does_not_save_invoice_without_human_review(self):
        record = crear_registro_factura(
            "factura.pdf",
            b"pdf",
            {"InvoiceId": "A-1"},
            {"InvoiceId": 0.5},
        )
        record["status"] = STATUS_CURRENT

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(InvoiceStorageError, "Confirma manualmente"):
                guardar_factura_demo(record, Path(directory) / "demo.sqlite3")

    def test_empty_analysis_cannot_be_saved(self):
        record = crear_registro_factura("factura.pdf", b"pdf", {})
        record["status"] = STATUS_CURRENT

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(InvoiceStorageError, "Confirma manualmente"):
                guardar_factura_demo(record, Path(directory) / "demo.sqlite3")


if __name__ == "__main__":
    unittest.main()

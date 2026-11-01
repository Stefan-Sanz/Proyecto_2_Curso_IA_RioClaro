import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from invoice_policy import (
    STATUS_CANCELLED,
    STATUS_CURRENT,
    STATUS_DUPLICATE,
    STATUS_PENDING,
    campos_para_revision_humana,
    crear_registro_factura,
    detectar_indicios_duplicidad,
    registrar_revision_humana,
    revision_humana_completa,
    registros_reportables,
)


class InvoicePolicyTests(unittest.TestCase):
    def test_new_invoice_requires_human_confirmation(self):
        invoice = crear_registro_factura("invoice.pdf", b"pdf", {"InvoiceId": "A-1"})

        self.assertEqual(invoice["status"], STATUS_PENDING)

    def test_duplicate_signals_are_reported_without_automatic_classification(self):
        first = crear_registro_factura(
            "first.pdf",
            b"first",
            {
                "InvoiceId": "A-1",
                "VendorName": "Proveedor Uno",
                "InvoiceDate": "2026-10-31",
                "InvoiceTotal": "$100.00",
            },
        )
        repeated = crear_registro_factura(
            "copy.pdf",
            b"copy",
            {
                "InvoiceId": "A-1",
                "VendorName": "Proveedor Uno",
                "InvoiceDate": "2026-10-31",
                "InvoiceTotal": "$100.00",
            },
        )

        signals = detectar_indicios_duplicidad(repeated, [first])

        self.assertEqual(
            signals[0]["reasons"],
            (
                "mismo folio",
                "mismo proveedor",
                "misma fecha de emisión",
                "mismo importe total",
            ),
        )
        self.assertEqual(repeated["status"], STATUS_PENDING)

    def test_repeated_file_is_flagged_even_when_extracted_fields_are_empty(self):
        first = crear_registro_factura("first.pdf", b"same file", {})
        repeated = crear_registro_factura("copy.pdf", b"same file", {})

        signals = detectar_indicios_duplicidad(repeated, [first])

        self.assertIn("archivo repetido", signals[0]["reasons"])

    def test_only_human_confirmed_current_invoices_are_reportable(self):
        records = [
            {"status": STATUS_CURRENT},
            {"status": STATUS_DUPLICATE},
            {"status": STATUS_CANCELLED},
            {"status": STATUS_PENDING},
        ]

        self.assertEqual(registros_reportables(records), [records[0]])

    def test_fields_below_threshold_or_without_confidence_require_review(self):
        fields = {
            "VendorName": "Proveedor",
            "VendorTaxId": "RFC-P",
            "CustomerName": "Cliente",
            "CustomerTaxId": "RFC-C",
            "InvoiceId": "RC-1",
            "SubTotal": "80",
            "InvoiceTotal": "100",
            "TotalTax": "20",
            "DueDate": "2026-11-30",
        }
        confidences = {
            "VendorName": 0.95,
            "VendorTaxId": 0.79,
            "CustomerName": 0.9,
            "CustomerTaxId": None,
            "InvoiceId": 0.79,
            "SubTotal": 0.8,
            "InvoiceTotal": 0.7,
            "TotalTax": 0.99,
            "DueDate": 0.1,
        }

        self.assertEqual(
            campos_para_revision_humana(fields, confidences),
            frozenset({"VendorTaxId", "CustomerTaxId", "InvoiceId", "InvoiceTotal"}),
        )

    def test_human_review_saves_corrections_and_unblocks_invoice(self):
        invoice = crear_registro_factura(
            "invoice.pdf",
            b"pdf",
            {"VendorName": "Río Claor", "InvoiceId": "RC-1"},
            {"VendorName": 0.6, "InvoiceId": 0.9},
        )

        self.assertFalse(revision_humana_completa(invoice))
        registrar_revision_humana(invoice, {"VendorName": "Río Claro"})

        self.assertEqual(invoice["fields"]["VendorName"], "Río Claro")
        self.assertTrue(revision_humana_completa(invoice))


if __name__ == "__main__":
    unittest.main()

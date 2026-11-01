import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from azure.core.exceptions import AzureError
from azure.ai.documentintelligence.models import DocumentField

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from config import REQUIRED_ENV_VARS
from document_service import DocumentAnalysisError, analizar_factura
from auth_service import crear_principal


FINANZAS = crear_principal(
    {
        "is_logged_in": True,
        "tid": "tenant-1",
        "oid": "finance-1",
        "roles": ["finanzas"],
    }
)


class AnalyzeInvoiceTests(unittest.TestCase):
    def setUp(self):
        self.environment = {name: f"value-for-{name}" for name in REQUIRED_ENV_VARS}
        self.client_patcher = patch("document_service.DocumentIntelligenceClient")
        self.client_class = self.client_patcher.start()
        self.addCleanup(self.client_patcher.stop)

    def test_returns_extracted_fields(self):
        document = SimpleNamespace(
            fields={
                "VendorName": DocumentField(
                    value_string="Río Claro",
                    content="Río Claro",
                    confidence=0.96,
                ),
                "InvoiceId": DocumentField(
                    value_string="RC-001",
                    confidence=0.62,
                ),
            }
        )
        self.client_class.return_value.begin_analyze_document.return_value.result.return_value = (
            SimpleNamespace(documents=[document])
        )

        with patch.dict(os.environ, self.environment, clear=True):
            result = analizar_factura(b"invoice", FINANZAS)

        self.assertEqual(
            result.fields,
            {"VendorName": "Río Claro", "InvoiceId": "RC-001"},
        )
        self.assertEqual(
            result.confidences,
            {"VendorName": 0.96, "InvoiceId": 0.62},
        )

    def test_missing_or_invalid_confidence_is_reported_as_unavailable(self):
        document = SimpleNamespace(
            fields={
                "VendorName": SimpleNamespace(value="Río Claro"),
                "InvoiceId": SimpleNamespace(value="RC-001", confidence=1.5),
            }
        )
        self.client_class.return_value.begin_analyze_document.return_value.result.return_value = (
            SimpleNamespace(documents=[document])
        )

        with patch.dict(os.environ, self.environment, clear=True):
            result = analizar_factura(b"invoice", FINANZAS)

        self.assertEqual(result.confidences, {"VendorName": None, "InvoiceId": None})

    def test_azure_failure_has_a_clear_message_without_service_details(self):
        self.client_class.return_value.begin_analyze_document.side_effect = AzureError(
            "private service response"
        )

        with patch.dict(os.environ, self.environment, clear=True):
            with self.assertRaises(DocumentAnalysisError) as raised:
                analizar_factura(b"invoice", FINANZAS)

        self.assertIn("Verifique la conexión", str(raised.exception))
        self.assertNotIn("private service response", str(raised.exception))

    def test_no_invoice_document_is_reported(self):
        self.client_class.return_value.begin_analyze_document.return_value.result.return_value = (
            SimpleNamespace(documents=[])
        )

        with patch.dict(os.environ, self.environment, clear=True):
            with self.assertRaisesRegex(DocumentAnalysisError, "no reconoció"):
                analizar_factura(b"not-an-invoice", FINANZAS)


if __name__ == "__main__":
    unittest.main()

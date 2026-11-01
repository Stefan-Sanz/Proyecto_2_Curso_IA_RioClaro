import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

import rag_service
from rag_service import KnowledgeSourceError, obtener_contexto, obtener_documentos
from auth_service import crear_principal, crear_principal_publico


CLIENTE = crear_principal_publico()
OBRERO = crear_principal(
    {
        "is_logged_in": True,
        "tid": "tenant-1",
        "oid": "worker-1",
        "roles": ["obrero"],
    }
)
FINANZAS = crear_principal(
    {
        "is_logged_in": True,
        "tid": "tenant-1",
        "oid": "finance-1",
        "roles": ["finanzas"],
    }
)
ADMINISTRADOR = crear_principal(
    {
        "is_logged_in": True,
        "tid": "tenant-1",
        "oid": "admin-1",
        "roles": ["administrador"],
    }
)


class KnowledgeContextTests(unittest.TestCase):
    def test_uses_the_project_data_folder_independent_of_working_directory(self):
        original_directory = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary_directory:
            try:
                os.chdir(temporary_directory)
                context = obtener_contexto(CLIENTE)
            finally:
                os.chdir(original_directory)

        self.assertIn("Horarios de Atención", context)
        self.assertIn("Política de Devoluciones", context)

    def test_documents_are_read_in_deterministic_order(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            data_dir = Path(temporary_directory)
            (data_dir / "z_document.txt").write_text("último", encoding="utf-8")
            (data_dir / "a_document.txt").write_text("primero", encoding="utf-8")

            with patch.object(rag_service, "DATA_DIR", data_dir):
                context = obtener_contexto(ADMINISTRADOR)

        self.assertLess(context.index("a_document.txt"), context.index("z_document.txt"))

    def test_missing_knowledge_documents_are_reported(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch.object(rag_service, "DATA_DIR", Path(temporary_directory)):
                with self.assertRaisesRegex(KnowledgeSourceError, "No se encontraron"):
                    obtener_contexto(ADMINISTRADOR)

    def test_roles_receive_only_their_approved_document_audiences(self):
        customer_context = obtener_contexto(CLIENTE)
        worker_context = obtener_contexto(OBRERO)
        finance_context = obtener_contexto(FINANZAS)

        self.assertIn("CATÁLOGO OFICIAL DE PRODUCTOS", customer_context)
        self.assertNotIn("INVENTARIO POR SUCURSAL", customer_context)
        self.assertNotIn("POLÍTICA DE GESTIÓN DE FACTURAS", customer_context)
        self.assertIn("INVENTARIO POR SUCURSAL", worker_context)
        self.assertNotIn("POLÍTICA DE GESTIÓN DE FACTURAS", worker_context)
        self.assertIn("POLÍTICA DE GESTIÓN DE FACTURAS", finance_context)
        self.assertNotIn("INVENTARIO POR SUCURSAL", finance_context)

    def test_customer_source_metadata_contains_only_public_documents(self):
        source_names = {
            document.filename for document in obtener_documentos(CLIENTE)
        }

        self.assertEqual(
            source_names,
            {
                "catalogo_productos_rio_claro.txt",
                "horarios.txt",
                "politica_devoluciones.txt",
            },
        )


if __name__ == "__main__":
    unittest.main()

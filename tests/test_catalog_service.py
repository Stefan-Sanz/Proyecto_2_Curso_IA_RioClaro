import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

import catalog_service
from catalog_service import (
    CatalogDataError,
    buscar_productos,
    cargar_catalogo,
    parse_catalog,
)


class CatalogServiceTests(unittest.TestCase):
    def test_loads_product_catalog_from_data(self):
        products = cargar_catalogo()

        self.assertGreaterEqual(len(products), 10)
        chlorine = next(product for product in products if product.code == "CL-001")
        self.assertEqual(chlorine.name, "Cloro Doméstico 1 L")
        self.assertEqual(chlorine.price, "$18.00 MXN")
        self.assertTrue(chlorine.details)

    def test_search_is_case_and_accent_insensitive(self):
        products = parse_catalog(
            """LÍNEA DE LIMPIEZA
Producto: Limpiador para Pisos
Código: PIS-001
Presentación: 1 litro
Precio: $42.00 MXN
"""
        )

        self.assertEqual(
            [product.code for product in buscar_productos(products, "LIMPIADOR pisos")],
            ["PIS-001"],
        )

    def test_search_filters_by_category_and_code(self):
        products = cargar_catalogo()

        result = buscar_productos(products, query="CL-001", category="Cloros")

        self.assertEqual([product.code for product in result], ["CL-001"])

    def test_missing_product_fields_are_reported(self):
        with self.assertRaisesRegex(CatalogDataError, "no tiene todos sus datos"):
            parse_catalog("Producto: Producto incompleto\nCódigo: P-001\n")

    def test_catalog_file_read_errors_are_reported(self):
        with patch.object(catalog_service, "CATALOG_FILE", Path("missing-catalog.txt")):
            with self.assertRaisesRegex(CatalogDataError, "No se pudo leer"):
                cargar_catalogo()


if __name__ == "__main__":
    unittest.main()

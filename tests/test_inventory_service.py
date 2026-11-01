import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from auth_service import AuthorizationError, crear_principal
from inventory_service import (
    INVENTORY_FILE,
    InventoryDataError,
    cargar_inventario,
    listar_existencias,
    parsear_inventario,
)


OBRERO = crear_principal(
    {
        "is_logged_in": True,
        "tid": "tenant-1",
        "oid": "worker-1",
        "roles": ["obrero"],
    }
)
CLIENTE = crear_principal(
    {
        "is_logged_in": True,
        "tid": "tenant-1",
        "oid": "customer-1",
        "roles": ["cliente"],
    }
)


class InventoryServiceTests(unittest.TestCase):
    def test_reads_all_five_branches_from_the_project_data_file(self):
        snapshot = parsear_inventario(INVENTORY_FILE.read_text(encoding="utf-8"))

        self.assertEqual(len(snapshot.quantities), 5)
        self.assertEqual(snapshot.updated_at.strftime("%d/%m/%Y"), "31/10/2026")
        self.assertIn("Cloro Doméstico 1 L", snapshot.quantities["Guadalajara"])

    def test_filters_by_branch_and_marks_availability_at_five_units(self):
        snapshot = parsear_inventario(
            """Fecha de actualización:
31/10/2026
SUCURSAL GUADALAJARA
Producto Disponible: 5 unidades
Producto No Disponible: 4 unidades
====================================================
SUCURSAL ZAPOPAN
Producto Disponible: 8 unidades
====================================================
SUCURSAL LEÓN
====================================================
SUCURSAL QUERÉTARO
====================================================
SUCURSAL AGUASCALIENTES
"""
        )

        rows = listar_existencias(snapshot, sucursal="Guadalajara")
        available_product = next(row for row in rows if row["Producto"] == "Producto Disponible")
        unavailable_product = next(
            row for row in rows if row["Producto"] == "Producto No Disponible"
        )

        self.assertEqual(available_product["Disponibilidad Guadalajara"], "Disponible")
        self.assertEqual(unavailable_product["Disponibilidad Guadalajara"], "No disponible")
        self.assertNotIn("Zapopan", available_product)

    def test_unlisted_branch_stock_is_not_reported_as_zero(self):
        snapshot = parsear_inventario(
            """Fecha de actualización: 31/10/2026
SUCURSAL GUADALAJARA
Cloro: 10 unidades
====================================================
SUCURSAL ZAPOPAN
====================================================
SUCURSAL LEÓN
====================================================
SUCURSAL QUERÉTARO
====================================================
SUCURSAL AGUASCALIENTES
"""
        )

        row = listar_existencias(snapshot)[0]
        self.assertEqual(row["Zapopan"], "Sin dato")
        self.assertEqual(row["Total registrado"], 10)
        self.assertEqual(row["Sucursales con dato"], "1/5")

    def test_missing_branch_is_an_explicit_data_error(self):
        with self.assertRaisesRegex(InventoryDataError, "Faltan datos"):
            parsear_inventario("Fecha de actualización: 31/10/2026")

    def test_inventory_backend_rejects_customer_role(self):
        with self.assertRaises(AuthorizationError):
            cargar_inventario(CLIENTE)


if __name__ == "__main__":
    unittest.main()

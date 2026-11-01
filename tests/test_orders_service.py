import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from auth_service import AuthorizationError, crear_principal, crear_principal_publico
from orders_service import (
    Order,
    OrderNotFoundError,
    OrdersSourceNotConfigured,
    UnconfiguredOrdersRepository,
    buscar_pedido_sintetico_en_mensaje,
    consultar_pedido_sintetico,
    consultar_pedido,
)


CLIENTE = crear_principal(
    {
        "is_logged_in": True,
        "tid": "tenant-1",
        "oid": "customer-1",
        "roles": ["cliente"],
    }
)
OTRO_CLIENTE = crear_principal(
    {
        "is_logged_in": True,
        "tid": "tenant-1",
        "oid": "customer-2",
        "roles": ["cliente"],
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


class InMemoryOrdersRepository:
    def __init__(self, order: Order | None):
        self.order = order

    def get_by_id(self, order_id: str) -> Order | None:
        return self.order if self.order and self.order.order_id == order_id else None


class OrdersServiceTests(unittest.TestCase):
    def test_customer_can_only_read_an_order_bound_to_their_identity(self):
        own_order = Order("order-1", "tenant-1", "customer-1", "En tránsito")
        other_order = Order("order-2", "tenant-1", "customer-2", "Entregado")

        self.assertEqual(
            consultar_pedido("order-1", CLIENTE, InMemoryOrdersRepository(own_order)),
            own_order,
        )
        with self.assertRaises(OrderNotFoundError):
            consultar_pedido("order-2", CLIENTE, InMemoryOrdersRepository(other_order))

    def test_order_lookup_requires_customer_role(self):
        with self.assertRaises(AuthorizationError):
            consultar_pedido(
                "order-1",
                FINANZAS,
                InMemoryOrdersRepository(None),
            )

    def test_order_lookup_requires_login_even_for_public_customer(self):
        with self.assertRaisesRegex(PermissionError, "iniciar sesión"):
            consultar_pedido(
                "order-1",
                crear_principal_publico(),
                InMemoryOrdersRepository(None),
            )

    def test_order_lookup_fails_closed_without_a_configured_source(self):
        with self.assertRaises(OrdersSourceNotConfigured):
            consultar_pedido("order-1", CLIENTE, UnconfiguredOrdersRepository())

    def test_order_lookup_requires_an_identifier(self):
        with self.assertRaises(ValueError):
            consultar_pedido(" ", CLIENTE, InMemoryOrdersRepository(None))

    def test_synthetic_order_requires_matching_order_number_and_customer_name(self):
        order = consultar_pedido_sintetico("RC-DEMO-1001", "ana lopez")

        self.assertEqual(order.customer_name, "Ana López")
        self.assertEqual(order.status, "En preparación")
        with self.assertRaises(OrderNotFoundError):
            consultar_pedido_sintetico("RC-DEMO-1001", "Carlos Méndez")

    def test_synthetic_order_can_be_found_in_a_customer_message(self):
        found, order = buscar_pedido_sintetico_en_mensaje(
            "¿Me ayudas con el pedido RC-DEMO-1002 de Carlos Mendez?"
        )

        self.assertTrue(found)
        self.assertIsNotNone(order)
        self.assertEqual(order.status, "En tránsito")

    def test_synthetic_order_message_without_customer_name_does_not_disclose_status(self):
        found, order = buscar_pedido_sintetico_en_mensaje(
            "¿Qué pasó con el pedido RC-DEMO-1002?"
        )

        self.assertTrue(found)
        self.assertIsNone(order)

    def test_order_tracking_question_without_order_details_is_intercepted(self):
        found, order = buscar_pedido_sintetico_en_mensaje(
            "¿Me pueden ayudar con el seguimiento?"
        )

        self.assertTrue(found)
        self.assertIsNone(order)

    def test_order_status_question_with_indefinite_article_is_intercepted(self):
        found, order = buscar_pedido_sintetico_en_mensaje(
            "¿Cuál es el estado de un pedido?"
        )

        self.assertTrue(found)
        self.assertIsNone(order)

    def test_order_status_statement_reported_by_customer_is_intercepted(self):
        found, order = buscar_pedido_sintetico_en_mensaje(
            "No tengo acceso a información sobre el estado de pedidos."
        )

        self.assertTrue(found)
        self.assertIsNone(order)

    def test_unrelated_customer_question_is_not_treated_as_order_tracking(self):
        found, order = buscar_pedido_sintetico_en_mensaje(
            "¿Qué productos de limpieza manejan?"
        )

        self.assertFalse(found)
        self.assertIsNone(order)


if __name__ == "__main__":
    unittest.main()

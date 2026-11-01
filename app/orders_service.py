from dataclasses import dataclass
import json
from pathlib import Path
import re
import unicodedata
from typing import Protocol

from auth_service import (
    Principal,
    ROLE_CLIENTE,
    exigir_autenticacion,
    exigir_rol,
)


class OrderNotFoundError(LookupError):
    """Raised when an order is absent or does not belong to the caller."""


class OrdersDemoDataError(RuntimeError):
    """Raised when the synthetic order examples cannot be loaded."""


class OrdersSourceNotConfigured(RuntimeError):
    """Raised when no approved order system is connected."""


@dataclass(frozen=True)
class Order:
    order_id: str
    customer_tenant_id: str
    customer_object_id: str
    status: str


@dataclass(frozen=True)
class DemoOrder:
    order_id: str
    customer_name: str
    status: str
    items: tuple[str, ...]
    updated_at: str


DEMO_ORDERS_FILE = (
    Path(__file__).resolve().parent.parent / "data" / "pedidos_demo.json"
)


def _normalizar_texto(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    return "".join(
        character
        for character in decomposed
        if unicodedata.category(character) != "Mn"
    )


def cargar_pedidos_sinteticos() -> list[DemoOrder]:
    try:
        contents = DEMO_ORDERS_FILE.read_text(encoding="utf-8")
        raw_orders = json.loads(contents)
    except (OSError, json.JSONDecodeError) as error:
        raise OrdersDemoDataError(
            "No se pudieron cargar los pedidos sintéticos de demostración."
        ) from error

    if not isinstance(raw_orders, list):
        raise OrdersDemoDataError("El archivo de pedidos sintéticos no es válido.")

    orders = []
    for raw_order in raw_orders:
        if (
            not isinstance(raw_order, dict)
            or not isinstance(raw_order.get("order_id"), str)
            or not isinstance(raw_order.get("customer_name"), str)
            or not isinstance(raw_order.get("status"), str)
            or not isinstance(raw_order.get("items"), list)
            or not all(isinstance(item, str) for item in raw_order["items"])
            or not isinstance(raw_order.get("updated_at"), str)
        ):
            raise OrdersDemoDataError(
                "El archivo contiene un pedido sintético con formato inválido."
            )
        orders.append(
            DemoOrder(
                order_id=raw_order["order_id"],
                customer_name=raw_order["customer_name"],
                status=raw_order["status"],
                items=tuple(raw_order["items"]),
                updated_at=raw_order["updated_at"],
            )
        )

    return orders


def consultar_pedido_sintetico(
    order_id: str,
    customer_name: str,
) -> DemoOrder:
    normalized_id = order_id.strip().casefold()
    normalized_name = _normalizar_texto(customer_name.strip())
    if not normalized_id or not normalized_name:
        raise ValueError("El número de pedido y el nombre del cliente son obligatorios.")

    order = next(
        (
            item
            for item in cargar_pedidos_sinteticos()
            if item.order_id.casefold() == normalized_id
            and _normalizar_texto(item.customer_name) == normalized_name
        ),
        None,
    )
    if order is None:
        raise OrderNotFoundError(
            "No se encontró ese pedido sintético para el nombre proporcionado."
        )
    return order


def buscar_pedido_sintetico_en_mensaje(
    message: str,
) -> tuple[bool, DemoOrder | None]:
    order_ids = re.findall(r"\bRC-DEMO-\d{4}\b", message, flags=re.IGNORECASE)
    normalized_message = _normalizar_texto(message)
    menciona_pedido = bool(re.search(r"\bpedidos?\b", normalized_message))
    menciona_estado = bool(
        re.search(
            r"\b(estado|estatus|seguimiento|rastreo|rastrear|entrega|entregado|"
            r"ubicacion|localizar)\b",
            normalized_message,
        )
    )
    is_order_inquiry = bool(
        order_ids
        or (menciona_pedido and menciona_estado)
        or re.search(r"\b(seguimiento|rastreo|rastrear)\b", normalized_message)
        or re.search(r"\bmi\s+pedido\b", normalized_message)
    )
    if not order_ids:
        return is_order_inquiry, None
    if len(set(order_id.casefold() for order_id in order_ids)) != 1:
        return True, None

    matching_customer_names = [
        order.customer_name
        for order in cargar_pedidos_sinteticos()
        if _normalizar_texto(order.customer_name) in normalized_message
    ]
    if len(matching_customer_names) != 1:
        return True, None

    try:
        order = consultar_pedido_sintetico(
            order_ids[0],
            matching_customer_names[0],
        )
    except OrderNotFoundError:
        return True, None
    return True, order


class OrderRepository(Protocol):
    def get_by_id(self, order_id: str) -> Order | None: ...


def consultar_pedido(
    order_id: str,
    principal: Principal,
    repository: OrderRepository,
) -> Order:
    exigir_autenticacion(principal)
    exigir_rol(principal, {ROLE_CLIENTE})
    normalized_order_id = order_id.strip()
    if not normalized_order_id:
        raise ValueError("El número de pedido es obligatorio.")

    order = repository.get_by_id(normalized_order_id)
    if (
        order is None
        or order.customer_tenant_id != principal.tenant_id
        or order.customer_object_id != principal.object_id
    ):
        raise OrderNotFoundError("No se encontró el pedido para la identidad autenticada.")

    return order


class UnconfiguredOrdersRepository:
    def get_by_id(self, order_id: str) -> Order | None:
        raise OrdersSourceNotConfigured(
            f"No está conectado el origen autorizado para consultar el pedido '{order_id}'."
        )

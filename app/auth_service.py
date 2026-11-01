from dataclasses import dataclass
from typing import Mapping


ROLE_CLIENTE = "cliente"
ROLE_OBRERO = "obrero"
ROLE_FINANZAS = "finanzas"
ROLE_ADMINISTRADOR = "administrador"

ROLES_VALIDOS = frozenset(
    {
        ROLE_CLIENTE,
        ROLE_OBRERO,
        ROLE_FINANZAS,
        ROLE_ADMINISTRADOR,
    }
)


class AuthenticationError(PermissionError):
    """Raised when a verified identity is not available."""


class AuthorizationError(PermissionError):
    """Raised when an identity is not allowed to perform an operation."""


@dataclass(frozen=True)
class Principal:
    tenant_id: str
    object_id: str
    email: str | None
    roles: frozenset[str]
    is_authenticated: bool = True


def crear_principal(claims: Mapping[str, object]) -> Principal:
    if claims.get("is_logged_in") is not True:
        raise AuthenticationError("Se requiere iniciar sesión.")

    tenant_id = claims.get("tid")
    object_id = claims.get("oid")
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        raise AuthenticationError("La identidad no incluye un tenant válido.")
    if not isinstance(object_id, str) or not object_id.strip():
        raise AuthenticationError("La identidad no incluye un usuario válido.")

    raw_roles = claims.get("roles", ())
    if isinstance(raw_roles, str):
        raw_roles = (raw_roles,)
    if not isinstance(raw_roles, (list, tuple, set, frozenset)):
        raw_roles = ()

    roles = frozenset(
        role.strip().casefold()
        for role in raw_roles
        if isinstance(role, str) and role.strip().casefold() in ROLES_VALIDOS
    )
    email = claims.get("preferred_username") or claims.get("email")

    return Principal(
        tenant_id=tenant_id.strip(),
        object_id=object_id.strip(),
        email=email if isinstance(email, str) else None,
        roles=roles,
    )


def crear_principal_publico() -> Principal:
    return Principal(
        tenant_id="",
        object_id="",
        email=None,
        roles=frozenset({ROLE_CLIENTE}),
        is_authenticated=False,
    )


def exigir_autenticacion(principal: Principal) -> None:
    if not principal.is_authenticated:
        raise AuthenticationError("Se requiere iniciar sesión para esta operación.")


def exigir_rol(principal: Principal, roles_permitidos: set[str] | frozenset[str]) -> None:
    if not principal.roles.intersection(roles_permitidos):
        raise AuthorizationError("No tiene permisos para realizar esta operación.")

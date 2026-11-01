import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from auth_service import (
    AuthenticationError,
    AuthorizationError,
    ROLE_CLIENTE,
    ROLE_FINANZAS,
    crear_principal,
    crear_principal_publico,
    exigir_autenticacion,
    exigir_rol,
)


class PrincipalTests(unittest.TestCase):
    def test_requires_an_authenticated_identity(self):
        with self.assertRaises(AuthenticationError):
            crear_principal({"is_logged_in": False})

    def test_requires_tenant_and_object_id(self):
        with self.assertRaises(AuthenticationError):
            crear_principal({"is_logged_in": True, "oid": "user-1"})

    def test_accepts_only_known_roles(self):
        principal = crear_principal(
            {
                "is_logged_in": True,
                "tid": "tenant-1",
                "oid": "user-1",
                "roles": ["CLIENTE", "unknown"],
                "preferred_username": "user@example.com",
            }
        )

        self.assertEqual(principal.roles, frozenset({ROLE_CLIENTE}))
        self.assertEqual(principal.email, "user@example.com")

    def test_backend_role_guard_rejects_unassigned_role(self):
        principal = crear_principal(
            {
                "is_logged_in": True,
                "tid": "tenant-1",
                "oid": "user-1",
                "roles": ["cliente"],
            }
        )

        with self.assertRaises(AuthorizationError):
            exigir_rol(principal, {ROLE_FINANZAS})

    def test_public_principal_can_read_public_content_without_login(self):
        principal = crear_principal_publico()

        exigir_rol(principal, {ROLE_CLIENTE})
        with self.assertRaises(AuthenticationError):
            exigir_autenticacion(principal)


if __name__ == "__main__":
    unittest.main()

from dataclasses import dataclass
from pathlib import Path

from auth_service import (
    Principal,
    ROLE_ADMINISTRADOR,
    ROLE_CLIENTE,
    ROLE_FINANZAS,
    ROLE_OBRERO,
    exigir_rol,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FUENTES_PUBLICAS = frozenset(
    {
        "catalogo_productos_rio_claro.txt",
        "horarios.txt",
        "politica_devoluciones.txt",
    }
)
FUENTES_INVENTARIO = frozenset({"inventario.txt"})
FUENTES_FINANZAS = frozenset({"politica_facturas_duplicadas_y_canceladas.txt"})


class KnowledgeSourceError(RuntimeError):
    """Raised when the business knowledge files cannot be loaded."""


@dataclass(frozen=True)
class KnowledgeDocument:
    filename: str
    content: str


def _fuentes_permitidas(principal: Principal) -> frozenset[str]:
    exigir_rol(
        principal,
        {ROLE_CLIENTE, ROLE_OBRERO, ROLE_FINANZAS, ROLE_ADMINISTRADOR},
    )
    if ROLE_ADMINISTRADOR in principal.roles:
        return frozenset(path.name for path in DATA_DIR.glob("*.txt"))
    if ROLE_FINANZAS in principal.roles:
        return FUENTES_PUBLICAS | FUENTES_FINANZAS
    if ROLE_OBRERO in principal.roles:
        return FUENTES_PUBLICAS | FUENTES_INVENTARIO
    return FUENTES_PUBLICAS


def obtener_documentos(principal: Principal) -> list[KnowledgeDocument]:
    fuentes_permitidas = _fuentes_permitidas(principal)
    archivos = sorted(
        archivo
        for archivo in DATA_DIR.glob("*.txt")
        if archivo.name in fuentes_permitidas
    )
    if not archivos:
        raise KnowledgeSourceError(
            "No se encontraron documentos de conocimiento autorizados para este rol."
        )

    documentos = []
    for archivo in archivos:
        try:
            contenido = archivo.read_text(encoding="utf-8")
        except OSError as error:
            raise KnowledgeSourceError(
                f"No se pudo leer el documento de conocimiento '{archivo.name}'."
            ) from error

        documentos.append(
            KnowledgeDocument(filename=archivo.name, content=contenido)
        )

    return documentos


def obtener_contexto(principal: Principal) -> str:
    return "".join(
        f"\n\n### {documento.filename}\n{documento.content}"
        for documento in obtener_documentos(principal)
    )
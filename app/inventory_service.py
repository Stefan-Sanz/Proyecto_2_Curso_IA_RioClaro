from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
import unicodedata
from typing import Mapping

from auth_service import Principal, ROLE_OBRERO, exigir_rol


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
INVENTORY_FILE = DATA_DIR / "inventario.txt"
UNIDADES_DISPONIBLES_MINIMAS = 5
SUCURSALES = (
    "Guadalajara",
    "Zapopan",
    "León",
    "Querétaro",
    "Aguascalientes",
)

_FECHA_RE = re.compile(r"^\s*Fecha de actualización:\s*(.*?)\s*$", re.IGNORECASE)
_SUCURSAL_RE = re.compile(r"^\s*SUCURSAL\s+(.+?)\s*$", re.IGNORECASE)
_EXISTENCIA_RE = re.compile(r"^\s*(.+?)\s*:\s*(\d+)\s+unidades\s*$", re.IGNORECASE)


class InventoryDataError(RuntimeError):
    """Raised when inventory data is absent or invalid."""


@dataclass(frozen=True)
class InventorySnapshot:
    updated_at: datetime
    quantities: Mapping[str, Mapping[str, int]]


def _normalizar(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    return "".join(character for character in decomposed if unicodedata.category(character) != "Mn")


def parsear_inventario(contents: str) -> InventorySnapshot:
    branch_lookup = {_normalizar(branch): branch for branch in SUCURSALES}
    quantities: dict[str, dict[str, int]] = {}
    current_branch: str | None = None
    updated_at: datetime | None = None
    awaiting_date = False

    for line_number, line in enumerate(contents.splitlines(), start=1):
        date_match = _FECHA_RE.match(line)
        if date_match:
            date_text = date_match.group(1).strip()
            if not date_text:
                awaiting_date = True
                continue
        elif awaiting_date and line.strip():
            date_text = line.strip()
            awaiting_date = False
        else:
            date_text = ""

        if date_text:
            try:
                updated_at = datetime.strptime(date_text, "%d/%m/%Y")
            except ValueError as error:
                raise InventoryDataError(
                    f"La fecha de actualización en la línea {line_number} no es válida."
                ) from error
            continue

        branch_match = _SUCURSAL_RE.match(line)
        if branch_match:
            branch_name = re.sub(
                r"\s*\([^)]*\)\s*$",
                "",
                branch_match.group(1),
            ).strip()
            current_branch = branch_lookup.get(_normalizar(branch_name))
            if current_branch is None:
                raise InventoryDataError(
                    f"La sucursal de la línea {line_number} no está en la lista autorizada."
                )
            quantities.setdefault(current_branch, {})
            continue

        if line.strip().upper().startswith("PRODUCTOS "):
            current_branch = None
            continue

        if current_branch is None:
            continue

        stock_match = _EXISTENCIA_RE.match(line)
        if not stock_match:
            continue

        product = stock_match.group(1).strip()
        if product in quantities[current_branch]:
            raise InventoryDataError(
                f"El producto '{product}' está duplicado en {current_branch}."
            )
        quantities[current_branch][product] = int(stock_match.group(2))

    if updated_at is None:
        raise InventoryDataError("El inventario no contiene una fecha de actualización válida.")

    missing_branches = [branch for branch in SUCURSALES if branch not in quantities]
    if missing_branches:
        raise InventoryDataError(
            "Faltan datos de estas sucursales: " + ", ".join(missing_branches) + "."
        )

    return InventorySnapshot(updated_at=updated_at, quantities=quantities)


def cargar_inventario(principal: Principal) -> InventorySnapshot:
    exigir_rol(principal, {ROLE_OBRERO})
    try:
        contents = INVENTORY_FILE.read_text(encoding="utf-8")
    except OSError as error:
        raise InventoryDataError(
            "No se pudo leer el archivo de inventario por sucursal."
        ) from error
    return parsear_inventario(contents)


def listar_existencias(
    snapshot: InventorySnapshot,
    sucursal: str | None = None,
    busqueda: str = "",
) -> list[dict[str, object]]:
    if sucursal is not None and sucursal not in SUCURSALES:
        raise ValueError("La sucursal seleccionada no es válida.")

    query = _normalizar(busqueda.strip())
    products = sorted(
        {
            product
            for branch_quantities in snapshot.quantities.values()
            for product in branch_quantities
            if not query or query in _normalizar(product)
        },
        key=_normalizar,
    )
    branches = (sucursal,) if sucursal else SUCURSALES

    rows = []
    for product in products:
        known_quantities = [
            snapshot.quantities[branch][product]
            for branch in SUCURSALES
            if product in snapshot.quantities[branch]
        ]
        row: dict[str, object] = {
            "Producto": product,
            "Total registrado": sum(known_quantities),
            "Sucursales con dato": f"{len(known_quantities)}/{len(SUCURSALES)}",
        }
        for branch in branches:
            quantity = snapshot.quantities[branch].get(product)
            row[branch] = quantity if quantity is not None else "Sin dato"
            row[f"Disponibilidad {branch}"] = (
                "Disponible"
                if quantity is not None and quantity >= UNIDADES_DISPONIBLES_MINIMAS
                else "No disponible"
                if quantity is not None
                else "Sin dato"
            )
        rows.append(row)

    return rows

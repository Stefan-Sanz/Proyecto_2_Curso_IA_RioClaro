from dataclasses import dataclass
from pathlib import Path
import unicodedata


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CATALOG_FILE = DATA_DIR / "catalogo_productos_rio_claro.txt"


class CatalogDataError(RuntimeError):
    """Raised when the product catalog is absent or invalid."""


@dataclass(frozen=True)
class CatalogProduct:
    name: str
    category: str
    code: str
    presentation: str
    price: str
    details: str


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    return "".join(
        character
        for character in decomposed
        if unicodedata.category(character) != "Mn"
    )


def parse_catalog(contents: str) -> list[CatalogProduct]:
    products: list[CatalogProduct] = []
    category = "General"
    current: dict[str, str] | None = None
    details: list[str] = []

    def save_current() -> None:
        if current is None:
            return
        required = ("name", "code", "presentation", "price")
        missing = [field for field in required if not current.get(field)]
        if missing:
            raise CatalogDataError(
                f"El producto '{current.get('name', 'sin nombre')}' "
                "no tiene todos sus datos de catálogo."
            )
        products.append(
            CatalogProduct(
                name=current["name"],
                category=current["category"],
                code=current["code"],
                presentation=current["presentation"],
                price=current["price"],
                details="\n".join(details).strip(),
            )
        )

    for line_number, line in enumerate(contents.splitlines(), start=1):
        stripped = line.strip()
        if stripped.upper().startswith("LÍNEA "):
            category_name = stripped[6:].strip()
            if category_name.casefold().startswith("de "):
                category_name = category_name[3:]
            category = category_name.title()
            continue
        if stripped.startswith("Producto:"):
            save_current()
            current = {
                "name": stripped.partition(":")[2].strip(),
                "category": category,
            }
            details = []
            if not current["name"]:
                raise CatalogDataError(
                    f"Falta el nombre de producto en la línea {line_number}."
                )
            continue
        if current is None or not stripped or set(stripped) <= {"-", "="}:
            continue

        key, separator, value = stripped.partition(":")
        if separator and key.casefold() in {"código", "presentación", "precio"}:
            field_name = {
                "código": "code",
                "presentación": "presentation",
                "precio": "price",
            }[key.casefold()]
            if current.get(field_name):
                raise CatalogDataError(
                    f"El producto '{current['name']}' repite el campo '{key}'."
                )
            current[field_name] = value.strip()
            continue

        details.append(stripped)

    save_current()
    if not products:
        raise CatalogDataError("El catálogo no contiene productos.")

    return products


def cargar_catalogo() -> list[CatalogProduct]:
    try:
        contents = CATALOG_FILE.read_text(encoding="utf-8")
    except OSError as error:
        raise CatalogDataError(
            "No se pudo leer el catálogo de productos."
        ) from error
    return parse_catalog(contents)


def buscar_productos(
    products: list[CatalogProduct],
    query: str = "",
    category: str | None = None,
) -> list[CatalogProduct]:
    query_terms = _normalize(query.strip()).split()
    normalized_category = _normalize(category) if category else None
    return [
        product
        for product in products
        if (not normalized_category or _normalize(product.category) == normalized_category)
        and (
            not query_terms
            or all(
                term
                in _normalize(
                    " ".join(
                        (
                            product.name,
                            product.code,
                            product.category,
                            product.presentation,
                            product.details,
                        )
                    )
                )
                for term in query_terms
            )
        )
    ]

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

REQUIRED_ENV_VARS = (
    "DOCUMENT_INTELLIGENCE_ENDPOINT",
    "DOCUMENT_INTELLIGENCE_KEY",
    "FOUNDRY_PROJECT_ENDPOINT",
    "FOUNDRY_API_KEY",
    "FOUNDRY_MODEL",
)
SPEECH_ENV_VARS = ("AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION")


class ConfigurationError(RuntimeError):
    """Raised when required application settings are unavailable."""


@dataclass(frozen=True)
class AppConfig:
    document_intelligence_endpoint: str
    document_intelligence_key: str
    foundry_project_endpoint: str
    foundry_api_key: str
    foundry_model: str
    speech_key: str | None
    speech_region: str | None

    @property
    def speech_configured(self) -> bool:
        return bool(self.speech_key and self.speech_region)


def load_config() -> AppConfig:
    values = {name: os.getenv(name, "").strip() for name in REQUIRED_ENV_VARS}
    missing = [name for name, value in values.items() if not value]

    if missing:
        variables = ", ".join(missing)
        raise ConfigurationError(
            f"Faltan variables de entorno requeridas: {variables}. "
            "Configure los valores en .env o en la configuración del servicio."
        )

    return AppConfig(
        document_intelligence_endpoint=values["DOCUMENT_INTELLIGENCE_ENDPOINT"],
        document_intelligence_key=values["DOCUMENT_INTELLIGENCE_KEY"],
        foundry_project_endpoint=values["FOUNDRY_PROJECT_ENDPOINT"],
        foundry_api_key=values["FOUNDRY_API_KEY"],
        foundry_model=values["FOUNDRY_MODEL"],
        speech_key=os.getenv(SPEECH_ENV_VARS[0], "").strip() or None,
        speech_region=os.getenv(SPEECH_ENV_VARS[1], "").strip() or None,
    )
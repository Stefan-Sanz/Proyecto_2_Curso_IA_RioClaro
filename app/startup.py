import json
import os
from pathlib import Path
import sys


OIDC_SETTINGS = (
    ("redirect_uri", "STREAMLIT_AUTH_REDIRECT_URI"),
    ("cookie_secret", "STREAMLIT_AUTH_COOKIE_SECRET"),
    ("client_id", "STREAMLIT_AUTH_CLIENT_ID"),
    ("client_secret", "STREAMLIT_AUTH_CLIENT_SECRET"),
    ("server_metadata_url", "STREAMLIT_AUTH_SERVER_METADATA_URL"),
)


def write_streamlit_secrets() -> Path:
    missing = [
        environment_name
        for _, environment_name in OIDC_SETTINGS
        if not os.environ.get(environment_name)
    ]
    if missing:
        raise RuntimeError(
            "Missing required OIDC App Settings: " + ", ".join(missing)
        )

    previous_umask = os.umask(0o077)
    try:
        secret_file = Path.home() / ".streamlit" / "secrets.toml"
        secret_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        secret_file.parent.chmod(0o700)
        content = ["[auth]"]
        content.extend(
            f"{key} = {json.dumps(os.environ[environment_name], ensure_ascii=True)}"
            for key, environment_name in OIDC_SETTINGS
        )
        secret_file.write_text("\n".join(content) + "\n", encoding="utf-8")
        secret_file.chmod(0o600)
        return secret_file
    finally:
        os.umask(previous_umask)


def main() -> None:
    write_streamlit_secrets()
    executable = sys.executable
    os.execv(
        executable,
        [
            executable,
            "-m",
            "streamlit",
            "run",
            "app/main.py",
            "--server.address=0.0.0.0",
            f"--server.port={os.environ.get('PORT') or '8000'}",
            "--server.headless=true",
        ],
    )


if __name__ == "__main__":
    main()

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from startup import OIDC_SETTINGS, write_streamlit_secrets


class WriteStreamlitSecretsTests(unittest.TestCase):
    def test_writes_global_toml_from_app_settings(self):
        settings = {
            environment_name: f"value-for-{environment_name}"
            for _, environment_name in OIDC_SETTINGS
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            home = Path(temporary_directory)
            with (
                patch.dict(os.environ, settings, clear=True),
                patch.object(Path, "home", return_value=home),
            ):
                secret_file = write_streamlit_secrets()

            self.assertEqual(
                secret_file,
                home / ".streamlit" / "secrets.toml",
            )
            content = secret_file.read_text(encoding="utf-8")
            self.assertTrue(content.startswith("[auth]\n"))
            for key, environment_name in OIDC_SETTINGS:
                self.assertIn(
                    f"{key} = {json.dumps(settings[environment_name], ensure_ascii=True)}",
                    content,
                )
            if os.name != "nt":
                self.assertEqual(
                    secret_file.stat().st_mode & 0o777,
                    0o600,
                )

    def test_missing_settings_are_reported_without_values(self):
        secret = "do-not-display-this"
        settings = {"STREAMLIT_AUTH_REDIRECT_URI": secret}

        with tempfile.TemporaryDirectory() as temporary_directory:
            with (
                patch.dict(os.environ, settings, clear=True),
                patch.object(Path, "home", return_value=Path(temporary_directory)),
            ):
                with self.assertRaises(RuntimeError) as raised:
                    write_streamlit_secrets()

        message = str(raised.exception)
        self.assertIn("STREAMLIT_AUTH_COOKIE_SECRET", message)
        self.assertNotIn(secret, message)


if __name__ == "__main__":
    unittest.main()

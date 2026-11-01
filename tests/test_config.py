import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from config import (
    ConfigurationError,
    REQUIRED_ENV_VARS,
    SPEECH_ENV_VARS,
    load_config,
)


class LoadConfigTests(unittest.TestCase):
    def test_missing_variables_are_reported_without_values(self):
        secret = "do-not-display-this"
        environment = {REQUIRED_ENV_VARS[1]: secret}

        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaises(ConfigurationError) as raised:
                load_config()

        message = str(raised.exception)
        self.assertIn(REQUIRED_ENV_VARS[0], message)
        self.assertNotIn(secret, message)

    def test_all_required_variables_are_loaded(self):
        environment = {name: f"value-for-{name}" for name in REQUIRED_ENV_VARS}

        with patch.dict(os.environ, environment, clear=True):
            config = load_config()

        self.assertEqual(
            config.document_intelligence_endpoint,
            environment["DOCUMENT_INTELLIGENCE_ENDPOINT"],
        )
        self.assertEqual(config.foundry_model, environment["FOUNDRY_MODEL"])
        self.assertFalse(config.speech_configured)

    def test_speech_configuration_is_optional_and_loaded_when_available(self):
        environment = {
            **{name: f"value-for-{name}" for name in REQUIRED_ENV_VARS},
            SPEECH_ENV_VARS[0]: "speech-key",
            SPEECH_ENV_VARS[1]: "westus",
        }

        with patch.dict(os.environ, environment, clear=True):
            config = load_config()

        self.assertTrue(config.speech_configured)
        self.assertEqual(config.speech_key, "speech-key")
        self.assertEqual(config.speech_region, "westus")


if __name__ == "__main__":
    unittest.main()

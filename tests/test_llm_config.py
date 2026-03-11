import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from humantext.llm.config import LLMConfig


class LLMConfigTests(unittest.TestCase):
    def test_from_mapping_prefers_real_env_over_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd_before = Path.cwd()
            cwd = Path(tmpdir)
            (cwd / ".env").write_text(
                "\n".join(
                    [
                        "HUMANTEXT_LLM_PROVIDER=dotenv-provider",
                        "HUMANTEXT_LLM_BASE_URL=http://localhost:11434/v1",
                        "HUMANTEXT_LLM_MODEL=dotenv-model",
                        "HUMANTEXT_LLM_API_KEY_ENV=HT_TEST_KEY",
                        "HT_TEST_KEY=dotenv-secret",
                    ]
                ),
                encoding="utf-8",
            )
            try:
                os.chdir(cwd)
                with patch.dict(
                    os.environ,
                    {
                        "HUMANTEXT_LLM_PROVIDER": "env-provider",
                        "HUMANTEXT_LLM_MODEL": "env-model",
                        "HT_TEST_KEY": "env-secret",
                    },
                    clear=True,
                ):
                    config = LLMConfig.from_mapping(None)
            finally:
                os.chdir(cwd_before)
            self.assertIsNotNone(config)
            assert config is not None
            self.assertEqual(config.provider, "env-provider")
            self.assertEqual(config.base_url, "http://localhost:11434/v1")
            self.assertEqual(config.model, "env-model")
            self.assertEqual(config.api_key, "env-secret")


if __name__ == "__main__":
    unittest.main()

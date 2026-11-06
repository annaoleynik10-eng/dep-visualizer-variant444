"""Тесты этапа 1: чтение конфигурации и обработка ошибок."""
import io
import os
import unittest
from contextlib import redirect_stderr

from depviz.__main__ import main
from depviz.config import load_config
from depviz.errors import ConfigError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIGS = os.path.join(ROOT, "tests", "configs")


def bad(name):
    """Путь к конфигу с ошибкой из tests/configs."""
    return os.path.join(CONFIGS, name + ".ini")


class LoadConfigTest(unittest.TestCase):
    """Проверка корректных и ошибочных конфигураций."""

    def test_real_config(self):
        """Обычный режим: все пять параметров прочитаны."""
        config = load_config(os.path.join(ROOT, "configs", "serde_json.ini"))
        self.assertEqual(config.package, "serde_json")
        self.assertEqual(config.repository, "https://index.crates.io")
        self.assertFalse(config.test_mode)
        self.assertEqual(config.version, "1.0.128")
        self.assertEqual(config.max_depth, 3)

    def test_test_mode_config(self):
        """Тестовый режим: путь к файлу превращается в абсолютный."""
        config = load_config(os.path.join(ROOT, "configs", "test_simple.ini"))
        self.assertTrue(config.test_mode)
        self.assertTrue(os.path.isabs(config.repository))

    def test_errors(self):
        """Каждый ошибочный параметр даёт понятное сообщение."""
        cases = {
            "no_section": "missing section",
            "broken": "invalid INI",
            "unknown_key": "unknown parameter: color",
            "no_package": "missing parameter: package",
            "empty_version": "missing parameter: version",
            "bad_package": "package: invalid name",
            "bad_url": "repository: expected http(s) URL",
            "bad_test_mode": "test_mode: expected true or false",
            "bad_version": "version: expected MAJOR.MINOR.PATCH",
            "bad_depth_text": "max_depth: expected integer",
            "bad_depth_zero": "max_depth: must be >= 1",
            "missing_test_file": "repository: test file not found",
            "bad_test_name": "capital latin letters",
        }
        for name, message in cases.items():
            with self.subTest(name=name):
                with self.assertRaises(ConfigError) as ctx:
                    load_config(bad(name))
                self.assertIn(message, str(ctx.exception))

    def test_missing_file(self):
        """Несуществующий файл конфигурации."""
        with self.assertRaises(ConfigError):
            load_config(bad("does_not_exist"))


class MainTest(unittest.TestCase):
    """Проверка вывода приложения."""

    def test_error_exit_code(self):
        """При ошибке — сообщение в stderr и код выхода 1."""
        err = io.StringIO()
        with redirect_stderr(err):
            code = main([bad("bad_depth_zero")])
        self.assertEqual(code, 1)
        self.assertIn("error: max_depth", err.getvalue())


if __name__ == "__main__":
    unittest.main()

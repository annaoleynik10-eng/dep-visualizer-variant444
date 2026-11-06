"""Тесты требований к версиям в стиле Cargo."""
import unittest

from depviz.semver import (VersionError, matches, parse_requirement,
                           parse_version)


def ok(version, req):
    """Подходит ли версия под требование."""
    return matches(parse_version(version), parse_requirement(req))


class SemverTest(unittest.TestCase):
    """Правила ^, ~, =, сравнения и *."""

    def test_order(self):
        """pre-release меньше релиза, числа сравниваются как числа."""
        self.assertLess(parse_version("1.0.0-beta"), parse_version("1.0.0"))
        self.assertLess(parse_version("1.2.9"), parse_version("1.10.0"))

    def test_caret(self):
        """^ и запись без оператора."""
        self.assertTrue(ok("1.9.0", "^1.2"))
        self.assertFalse(ok("2.0.0", "^1.2"))
        self.assertTrue(ok("0.3.9", "0.3.1"))
        self.assertFalse(ok("0.4.0", "^0.3"))
        self.assertFalse(ok("0.0.4", "^0.0.3"))
        self.assertFalse(ok("1.1.0", "^1.2"))

    def test_tilde_and_exact(self):
        """~ разрешает только patch, = — точную версию."""
        self.assertTrue(ok("1.2.9", "~1.2.3"))
        self.assertFalse(ok("1.3.0", "~1.2.3"))
        self.assertTrue(ok("1.4.2", "~1"))
        self.assertTrue(ok("1.2.3", "=1.2.3"))
        self.assertFalse(ok("1.2.4", "=1.2.3"))

    def test_ranges_and_wildcards(self):
        """Несколько сравнений через запятую и *."""
        self.assertTrue(ok("1.5.0", ">=1.2, <2"))
        self.assertFalse(ok("2.0.0", ">=1.2, <2"))
        self.assertTrue(ok("7.0.0", "*"))
        self.assertTrue(ok("1.2.7", "1.2.*"))
        self.assertFalse(ok("1.3.0", "1.2.*"))

    def test_prerelease(self):
        """pre-release выбирается, только если запрошен явно."""
        self.assertFalse(ok("2.0.0-rc.1", "^1"))
        self.assertTrue(ok("2.0.0-rc.2", ">=2.0.0-rc.1"))

    def test_bad(self):
        """Неверная запись."""
        with self.assertRaises(VersionError):
            parse_version("1.0")
        with self.assertRaises(VersionError):
            parse_requirement("^abc")


if __name__ == "__main__":
    unittest.main()

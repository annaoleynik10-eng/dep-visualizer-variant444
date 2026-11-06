"""Тесты этапа 2: чтение индекса Cargo и прямые зависимости."""
import json
import unittest

from depviz.cargo import (CargoRegistry, NotFoundError, RegistryError,
                          index_path)


def line(name, vers, deps=(), yanked=False):
    """Строка индекса для версии пакета."""
    return json.dumps({"name": name, "vers": vers, "yanked": yanked,
                       "deps": list(deps)})


def dep(name, req, kind="normal", optional=False, package=None):
    """Описание зависимости в формате индекса."""
    item = {"name": name, "req": req, "kind": kind, "optional": optional,
            "target": None}
    if package:
        item["package"] = package
    return item


INDEX = {
    "https://example.org/3/a/app": "\n".join([
        line("app", "1.0.0", [dep("libx", "^1.0")]),
        line("app", "2.0.0", [
            dep("libx", "^1.2"),
            dep("liby", "~0.3", kind="build"),
            dep("tester", "1", kind="dev"),
            dep("extra", "^2", optional=True),
            dep("short", "^1", package="real-name"),
        ]),
    ]),
}


def fake_fetch(url):
    """Подменить скачивание: вернуть данные из словаря INDEX."""
    if url not in INDEX:
        raise NotFoundError(url)
    return INDEX[url]


class IndexPathTest(unittest.TestCase):
    """Путь к файлу пакета в индексе."""

    def test_paths(self):
        """Правила для имён разной длины."""
        self.assertEqual(index_path("a"), "1/a")
        self.assertEqual(index_path("ab"), "2/ab")
        self.assertEqual(index_path("abc"), "3/a/abc")
        self.assertEqual(index_path("Serde"), "se/rd/serde")


class RegistryTest(unittest.TestCase):
    """Получение прямых зависимостей заданной версии."""

    registry = CargoRegistry("https://example.org/", fake_fetch)

    def test_direct_dependencies(self):
        """Берутся normal и build, без dev и optional; package = имя."""
        names = [d.name for d in
                 self.registry.direct_dependencies("app", "2.0.0")]
        self.assertEqual(names, ["libx", "liby", "real-name"])

    def test_version_matters(self):
        """У другой версии — свои зависимости."""
        deps = self.registry.direct_dependencies("app", "1.0.0")
        self.assertEqual([(d.name, d.req) for d in deps],
                         [("libx", "^1.0")])

    def test_unknown_package(self):
        """Пакета нет в репозитории."""
        with self.assertRaises(RegistryError) as ctx:
            self.registry.releases("nothing")
        self.assertIn("not found in repository", str(ctx.exception))

    def test_unknown_version(self):
        """Версии нет у пакета."""
        with self.assertRaises(RegistryError):
            self.registry.release("app", "9.9.9")

    def test_cache(self):
        """Файл пакета скачивается один раз."""
        calls = []
        registry = CargoRegistry("https://example.org",
                                 lambda url: calls.append(url) or
                                 fake_fetch(url))
        registry.releases("app")
        registry.releases("app")
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()

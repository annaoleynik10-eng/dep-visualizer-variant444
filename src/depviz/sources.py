"""Источники зависимостей: реестр Cargo и файл тестового репозитория.

У обоих источников одинаковый набор методов: root, dependencies и
label. Поэтому алгоритм обхода графа не зависит от того, откуда
берутся данные.
"""
import re

from depviz.cargo import CargoRegistry, RegistryError
from depviz.errors import DepVizError
from depviz.semver import VersionError, matches, parse_requirement, \
    parse_version

TEST_NAME = re.compile(r"^[A-Z]+$")


class TestRepoError(DepVizError):
    """Ошибка в файле тестового репозитория."""


def parse_test_line(text, number):
    """Разобрать строку 'A: B C' в (пакет, [зависимости])."""
    name, colon, rest = text.partition(":")
    name = name.strip()
    deps = rest.split()
    if not colon:
        raise TestRepoError(f"line {number}: expected 'NAME: DEPS'")
    for item in [name] + deps:
        if not TEST_NAME.match(item):
            raise TestRepoError(
                f"line {number}: bad package name '{item}' (A-Z only)")
    return name, deps


def load_test_repo(path):
    """Прочитать файл тестового репозитория в словарь пакет -> список."""
    try:
        with open(path, encoding="utf-8") as file:
            lines = file.read().splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise TestRepoError(f"cannot read test repository: {exc}") from None
    graph = {}
    for number, text in enumerate(lines, start=1):
        text = text.split("#", 1)[0].strip()
        if not text:
            continue
        name, deps = parse_test_line(text, number)
        if name in graph:
            raise TestRepoError(f"line {number}: package {name} repeated")
        graph[name] = deps
    return graph


def unique(items):
    """Убрать повторы, сохранив порядок."""
    return list(dict.fromkeys(items))


class FileSource:
    """Тестовый репозиторий: пакеты — большие латинские буквы."""

    def __init__(self, path):
        """Загрузить граф из файла."""
        self.graph = load_test_repo(path)
        self.warnings = []

    def root(self, name, _version):
        """Корень графа; версия в тестовом режиме не используется."""
        if name not in self.graph:
            raise TestRepoError(f"package {name} not found in test repository")
        return name

    def dependencies(self, node):
        """Прямые зависимости пакета."""
        return unique(self.graph.get(node, []))

    @staticmethod
    def label(node):
        """Подпись вершины."""
        return node


class RegistrySource:
    """Реальный реестр Cargo: вершина — пара (имя, версия)."""

    def __init__(self, url, fetch=None):
        """Создать доступ к индексу по URL."""
        self.registry = CargoRegistry(url, fetch) if fetch else \
            CargoRegistry(url)
        self.warnings = []

    def root(self, name, version):
        """Проверить, что версия существует, и вернуть корень."""
        self.registry.release(name, version)
        return (name, version)

    def resolve(self, name, req):
        """Выбрать максимальную невыдернутую версию под требование."""
        rules = parse_requirement(req)
        candidates = [(parse_version(item["vers"]), item["vers"])
                      for item in self.registry.releases(name)
                      if not item.get("yanked")]
        suitable = [pair for pair in candidates if matches(pair[0], rules)]
        if not suitable:
            raise RegistryError(f"no version of {name} matches '{req}'")
        return max(suitable)[1]

    def dependencies(self, node):
        """Прямые зависимости с подобранными версиями."""
        result = []
        for dep in self.registry.direct_dependencies(*node):
            try:
                result.append((dep.name, self.resolve(dep.name, dep.req)))
            except (RegistryError, VersionError) as exc:
                self.warnings.append(f"{self.label(node)}: {exc}")
        return unique(result)

    @staticmethod
    def label(node):
        """Подпись вершины: 'имя версия'."""
        return f"{node[0]} {node[1]}"


def make_source(config):
    """Выбрать источник по параметру test_mode."""
    if config.test_mode:
        return FileSource(config.repository)
    return RegistrySource(config.repository)

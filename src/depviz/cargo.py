"""Получение зависимостей пакетов из индекса реестра Cargo (crates.io).

Индекс реестра — это набор текстовых файлов, по одному на пакет.
Каждая строка файла — JSON с описанием одной версии пакета и списком
её зависимостей. Файл пакета лежит по пути, зависящему от длины имени:
1/a, 2/ab, 3/a/abc, se/rd/serde.
"""
import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from depviz.errors import DepVizError

ONE_CHAR = 1
TWO_CHARS = 2
THREE_CHARS = 3
PREFIX_END = 2
SECOND_PART_END = 4
HTTP_NOT_FOUND = 404
TIMEOUT_SECONDS = 20
USED_KINDS = ("normal", "build")
USER_AGENT = "depviz/1.0 (student project)"


class RegistryError(DepVizError):
    """Ошибка при получении данных из репозитория пакетов."""


class NotFoundError(RegistryError):
    """Файл пакета отсутствует в репозитории (HTTP 404)."""


@dataclass
class Dependency:
    """Одна зависимость из описания версии пакета."""

    name: str
    req: str
    kind: str
    optional: bool
    target: str

    def is_used(self):
        """Зависимость нужна для сборки: не dev и не optional."""
        return self.kind in USED_KINDS and not self.optional


def index_path(name):
    """Вернуть путь к файлу пакета внутри индекса."""
    name = name.lower()
    size = len(name)
    if size in (ONE_CHAR, TWO_CHARS):
        return f"{size}/{name}"
    if size == THREE_CHARS:
        return f"{size}/{name[0]}/{name}"
    return f"{name[:PREFIX_END]}/{name[PREFIX_END:SECOND_PART_END]}/{name}"


def download(url):
    """Скачать текст по URL средствами стандартной библиотеки."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == HTTP_NOT_FOUND:
            raise NotFoundError(f"not found: {url}") from None
        raise RegistryError(f"HTTP error {exc.code}: {url}") from None
    except (urllib.error.URLError, OSError) as exc:
        raise RegistryError(f"cannot reach repository: {exc}") from None


def parse_dependency(item):
    """Превратить словарь из индекса в Dependency.

    Поле package есть, если зависимость переименована: тогда настоящее
    имя пакета записано в нём, а name — это псевдоним.
    """
    return Dependency(
        name=item.get("package") or item["name"],
        req=item.get("req", "*"),
        kind=item.get("kind") or "normal",
        optional=bool(item.get("optional")),
        target=item.get("target") or "",
    )


class CargoRegistry:
    """Доступ к индексу реестра Cargo по URL с кэшем скачанных файлов."""

    def __init__(self, base_url, fetch=download):
        """Запомнить адрес индекса и функцию скачивания."""
        self.base_url = base_url.rstrip("/")
        self.fetch = fetch
        self.cache = {}

    def releases(self, name):
        """Вернуть список всех версий пакета (словари из индекса)."""
        if name not in self.cache:
            url = f"{self.base_url}/{index_path(name)}"
            try:
                text = self.fetch(url)
            except NotFoundError:
                raise RegistryError(
                    f"package {name} not found in repository") from None
            try:
                self.cache[name] = [json.loads(line)
                                    for line in text.splitlines()
                                    if line.strip()]
            except json.JSONDecodeError as exc:
                raise RegistryError(
                    f"bad index data for {name}: {exc}") from None
        return self.cache[name]

    def release(self, name, version):
        """Найти описание конкретной версии пакета."""
        for item in self.releases(name):
            if item.get("vers") == version:
                return item
        raise RegistryError(f"version {version} of {name} not found")

    def dependencies(self, name, version):
        """Все зависимости версии пакета (включая dev и optional)."""
        item = self.release(name, version)
        return [parse_dependency(dep) for dep in item.get("deps", [])]

    def direct_dependencies(self, name, version):
        """Прямые зависимости, нужные для сборки пакета."""
        return [dep for dep in self.dependencies(name, version)
                if dep.is_used()]

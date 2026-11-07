"""Чтение и проверка конфигурационного файла формата INI."""
import configparser
import os
import re
from dataclasses import dataclass

from depviz.errors import ConfigError

SECTION = "depviz"
KEYS = ("package", "repository", "test_mode", "version", "max_depth")
OPTIONAL = {"mode": "graph", "output_dir": "out"}
MODES = ("graph", "reverse", "mermaid")
MIN_DEPTH = 1
CRATE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
TEST_NAME = re.compile(r"^[A-Z]+$")
VERSION = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$")
URL = re.compile(r"^https?://[^\s/]+\S*$")
TRUE_WORDS = ("true", "yes", "on", "1")
FALSE_WORDS = ("false", "no", "off", "0")


@dataclass
class Config:
    """Параметры, настраиваемые пользователем."""

    package: str
    repository: str
    test_mode: bool
    version: str
    max_depth: int
    mode: str = OPTIONAL["mode"]
    output_dir: str = OPTIONAL["output_dir"]

    def items(self):
        """Вернуть пары (ключ, значение) в порядке объявления."""
        return [(key, getattr(self, key))
                for key in KEYS + tuple(OPTIONAL)]


def read_section(path):
    """Прочитать секцию [depviz] и вернуть словарь строковых значений."""
    if not os.path.isfile(path):
        raise ConfigError(f"config file not found: {path}")
    parser = configparser.ConfigParser()
    try:
        parser.read(path, encoding="utf-8")
    except (configparser.Error, UnicodeDecodeError) as exc:
        first_line = str(exc).splitlines()[0]
        raise ConfigError(f"invalid INI file: {first_line}") from exc
    if not parser.has_section(SECTION):
        raise ConfigError(f"missing section [{SECTION}]")
    section = parser[SECTION]
    unknown = sorted(set(section) - set(KEYS) - set(OPTIONAL))
    if unknown:
        raise ConfigError(f"unknown parameter: {unknown[0]}")
    for key in KEYS:
        if not section.get(key, "").strip():
            raise ConfigError(f"missing parameter: {key}")
    values = {key: section[key].strip() for key in KEYS}
    for key, default in OPTIONAL.items():
        values[key] = section.get(key, "").strip() or default
    return values


def parse_bool(value):
    """Преобразовать строку test_mode в True или False."""
    word = value.lower()
    if word in TRUE_WORDS:
        return True
    if word in FALSE_WORDS:
        return False
    raise ConfigError(f"test_mode: expected true or false, got '{value}'")


def parse_depth(value):
    """Преобразовать max_depth в целое число не меньше MIN_DEPTH."""
    try:
        depth = int(value)
    except ValueError:
        raise ConfigError(
            f"max_depth: expected integer, got '{value}'") from None
    if depth < MIN_DEPTH:
        raise ConfigError(f"max_depth: must be >= {MIN_DEPTH}, got {depth}")
    return depth


def check_package(name, test_mode):
    """Проверить имя пакета: в тестовом режиме — только A-Z."""
    pattern = TEST_NAME if test_mode else CRATE_NAME
    if not pattern.match(name):
        rule = "capital latin letters" if test_mode else \
            "latin letters, digits, '_' and '-'"
        raise ConfigError(f"package: invalid name '{name}' ({rule})")
    return name


def check_repository(value, test_mode, base_dir):
    """Проверить URL репозитория или путь к файлу тестового репозитория."""
    if not test_mode:
        if not URL.match(value):
            raise ConfigError(
                f"repository: expected http(s) URL, got '{value}'")
        return value.rstrip("/")
    path = os.path.normpath(os.path.join(base_dir, value))
    if not os.path.isfile(path):
        raise ConfigError(f"repository: test file not found: {value}")
    return path


def check_version(value):
    """Проверить версию пакета в формате semver (например, 1.0.2)."""
    if not VERSION.match(value):
        raise ConfigError(
            f"version: expected MAJOR.MINOR.PATCH, got '{value}'")
    return value


def check_mode(value):
    """Проверить режим вывода."""
    if value not in MODES:
        raise ConfigError(
            f"mode: expected one of {', '.join(MODES)}, got '{value}'")
    return value


def load_config(path):
    """Прочитать файл, проверить все параметры и вернуть Config."""
    raw = read_section(path)
    test_mode = parse_bool(raw["test_mode"])
    base_dir = os.path.dirname(os.path.abspath(path))
    return Config(
        package=check_package(raw["package"], test_mode),
        repository=check_repository(raw["repository"], test_mode, base_dir),
        test_mode=test_mode,
        version=check_version(raw["version"]),
        max_depth=parse_depth(raw["max_depth"]),
        mode=check_mode(raw["mode"]),
        output_dir=raw["output_dir"],
    )

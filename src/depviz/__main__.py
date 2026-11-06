"""Точка входа: python -m depviz [путь к config.ini]."""
import argparse
import sys

from depviz.cargo import CargoRegistry
from depviz.config import load_config
from depviz.errors import DepVizError

DEFAULT_CONFIG = "config.ini"


def parse_args(argv):
    """Разобрать аргументы командной строки."""
    parser = argparse.ArgumentParser(
        prog="depviz",
        description="Визуализация графа зависимостей пакетов Cargo")
    parser.add_argument("config", nargs="?", default=DEFAULT_CONFIG,
                        help="путь к конфигурационному файлу INI")
    return parser.parse_args(argv)


def describe(dep):
    """Строка для вывода одной зависимости."""
    extra = f" [{dep.kind}]" if dep.kind != "normal" else ""
    target = f" (target: {dep.target})" if dep.target else ""
    return f"  {dep.name} {dep.req}{extra}{target}"


def print_direct(config, registry):
    """Вывести прямые зависимости пакета заданной версии."""
    deps = registry.dependencies(config.package, config.version)
    used = [dep for dep in deps if dep.is_used()]
    print(f"{config.package} {config.version}: "
          f"direct dependencies ({len(used)})")
    for dep in used:
        print(describe(dep))
    skipped = len(deps) - len(used)
    if skipped:
        print(f"skipped dev/optional dependencies: {skipped}")


def run(config):
    """Выполнить работу приложения согласно конфигурации."""
    if config.test_mode:
        raise DepVizError("test repository mode is not implemented yet")
    print_direct(config, CargoRegistry(config.repository))


def main(argv=None):
    """Загрузить конфигурацию и запустить приложение; вернуть код выхода."""
    args = parse_args(argv)
    try:
        config = load_config(args.config)
        run(config)
    except DepVizError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

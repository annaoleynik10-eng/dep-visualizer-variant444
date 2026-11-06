"""Точка входа: python -m depviz [путь к config.ini]."""
import argparse
import sys

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


def format_value(value):
    """Показать значение параметра так, как оно пишется в INI."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def run(config):
    """Выполнить работу приложения: вывести параметры ключ = значение."""
    for key, value in config.items():
        print(f"{key} = {format_value(value)}")


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

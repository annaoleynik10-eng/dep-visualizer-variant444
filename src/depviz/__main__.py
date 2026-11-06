"""Точка входа: python -m depviz [путь к config.ini]."""
import argparse
import sys

from depviz.config import load_config
from depviz.errors import DepVizError
from depviz.graph import build_graph, find_cycles
from depviz.sources import make_source

DEFAULT_CONFIG = "config.ini"


def parse_args(argv):
    """Разобрать аргументы командной строки."""
    parser = argparse.ArgumentParser(
        prog="depviz",
        description="Визуализация графа зависимостей пакетов Cargo")
    parser.add_argument("config", nargs="?", default=DEFAULT_CONFIG,
                        help="путь к конфигурационному файлу INI")
    return parser.parse_args(argv)


def print_graph(graph, label, max_depth):
    """Вывести граф: вершины в порядке BFS и их зависимости."""
    print(f"dependency graph of {label(graph.root)} "
          f"(max_depth = {max_depth})")
    print(f"packages: {len(graph.edges)}, edges: {graph.edge_count()}")
    for node, children in graph.edges.items():
        text = ", ".join(label(child) for child in children)
        if node in graph.cut:
            text = "... (max depth reached)"
        arrow = f" -> {text}" if text else ""
        print(f"  [{graph.depth[node]}] {label(node)}{arrow}")


def print_cycles(cycles, label):
    """Вывести найденные циклические зависимости."""
    if not cycles:
        print("cycles: none")
        return
    print(f"cycles: {len(cycles)}")
    for cycle in cycles:
        print("  " + " -> ".join(label(node) for node in cycle))


def run(config):
    """Построить граф зависимостей и вывести его."""
    source = make_source(config)
    root = source.root(config.package, config.version)
    graph = build_graph(root, source.dependencies, config.max_depth)
    print_graph(graph, source.label, config.max_depth)
    print_cycles(find_cycles(graph), source.label)
    for warning in source.warnings:
        print(f"warning: {warning}", file=sys.stderr)


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

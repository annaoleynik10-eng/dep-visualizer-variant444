"""Тесты этапа 4: обратные зависимости."""
import io
import os
import unittest
from contextlib import redirect_stdout

from depviz.__main__ import main
from depviz.config import load_config
from depviz.errors import ConfigError, DepVizError
from depviz.graph import build_graph, reverse_edges
from depviz.sources import FileSource, RegistrySource

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOS = os.path.join(ROOT, "tests", "repos")


def reverse_of(repo, root, depth):
    """Граф обратных зависимостей по тестовому репозиторию."""
    source = FileSource(os.path.join(REPOS, repo + ".txt"))
    return build_graph(source.root(root, None), source.reverse_source(),
                       depth)


class ReverseTest(unittest.TestCase):
    """Обратный обход тем же BFS."""

    def test_reverse_edges(self):
        """Рёбра разворачиваются."""
        self.assertEqual(reverse_edges({"A": ["B"], "B": []}),
                         {"A": [], "B": ["A"]})

    def test_common_dependency(self):
        """От D зависят B и C напрямую и A транзитивно."""
        graph = reverse_of("simple", "D", 10)
        self.assertEqual(graph.edges["D"], ["B", "C"])
        self.assertEqual(set(graph.edges), {"D", "B", "C", "A"})

    def test_root_package(self):
        """От корневого пакета никто не зависит."""
        self.assertEqual(list(reverse_of("simple", "A", 10).edges), ["A"])

    def test_depth_and_cycle(self):
        """Глубина ограничивает обратный обход, цикл не мешает."""
        self.assertEqual(list(reverse_of("chain", "F", 2).edges),
                         ["F", "E", "D"])
        self.assertEqual(len(reverse_of("cycle", "D", 10).edges), 4)

    def test_undescribed_leaf(self):
        """Лист K есть только в списке зависимостей — его находим."""
        graph = reverse_of("complex", "K", 10)
        self.assertEqual(graph.edges["K"], ["D"])

    def test_registry_not_supported(self):
        """Для реестра Cargo режим reverse даёт понятную ошибку."""
        with self.assertRaises(DepVizError):
            RegistrySource("https://example.org").reverse_source()

    def test_mode_option(self):
        """Параметр mode: по умолчанию graph, ошибка для неизвестного."""
        config = load_config(os.path.join(ROOT, "configs", "test_simple.ini"))
        self.assertEqual(config.mode, "graph")
        with self.assertRaises(ConfigError):
            load_config(os.path.join(ROOT, "tests", "configs",
                                     "bad_mode.ini"))

    def test_main_output(self):
        """Вывод режима reverse."""
        out = io.StringIO()
        with redirect_stdout(out):
            main([os.path.join(ROOT, "configs", "reverse_simple_d.ini")])
        self.assertIn("packages depending on D: B, C, A", out.getvalue())


if __name__ == "__main__":
    unittest.main()

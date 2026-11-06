"""Тесты этапа 3: BFS, глубина, циклы, тестовый репозиторий."""
import json
import os
import unittest

from depviz.graph import build_graph, find_cycles
from depviz.sources import FileSource, RegistrySource, TestRepoError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOS = os.path.join(ROOT, "tests", "repos")


def graph_of(repo, root, depth):
    """Построить граф по файлу тестового репозитория."""
    source = FileSource(os.path.join(REPOS, repo + ".txt"))
    return build_graph(source.root(root, None), source.dependencies, depth)


class BfsTest(unittest.TestCase):
    """Обход в ширину."""

    def test_order_and_depth(self):
        """Вершины в порядке BFS, общая зависимость D один раз."""
        graph = graph_of("simple", "A", 5)
        self.assertEqual(list(graph.edges), ["A", "B", "C", "D", "E"])
        self.assertEqual(graph.depth["D"], 2)
        self.assertEqual(graph.edge_count(), 5)

    def test_max_depth(self):
        """Глубже max_depth не идём, обрезанные вершины помечены."""
        graph = graph_of("chain", "A", 2)
        self.assertEqual(list(graph.edges), ["A", "B", "C"])
        self.assertEqual(graph.cut, {"C"})

    def test_cycle_terminates(self):
        """Цикл не приводит к бесконечному обходу и находится."""
        graph = graph_of("cycle", "A", 10)
        self.assertEqual(len(graph.edges), 4)
        self.assertEqual(find_cycles(graph), [["A", "B", "C", "A"]])

    def test_self_loop(self):
        """Пакет, зависящий сам от себя."""
        self.assertEqual(find_cycles(graph_of("self", "A", 10)),
                         [["A", "A"]])

    def test_complex(self):
        """Большой граф с двумя циклами и неописанным листом."""
        graph = graph_of("complex", "A", 10)
        self.assertIn("K", graph.edges)
        cycles = find_cycles(graph)
        self.assertIn(["E", "G", "E"], cycles)
        self.assertEqual(len(cycles), 2)

    def test_no_cycles(self):
        """Граф без циклов."""
        self.assertEqual(find_cycles(graph_of("simple", "A", 5)), [])


class TestRepoTest(unittest.TestCase):
    """Ошибки файла тестового репозитория."""

    def test_errors(self):
        """Неверный формат, имя и неизвестный корень."""
        for repo in ("bad_format", "bad_name"):
            with self.subTest(repo=repo), self.assertRaises(TestRepoError):
                FileSource(os.path.join(REPOS, repo + ".txt"))
        with self.assertRaises(TestRepoError):
            FileSource(os.path.join(REPOS, "simple.txt")).root("Z", None)


def fake_index(url):
    """Маленький индекс: app -> lib (^1), lib -> app (цикл)."""
    data = {
        "3/a/app": [{"vers": "1.0.0", "deps": [
            {"name": "lib", "req": "^1", "kind": "normal"}]}],
        "3/l/lib": [
            {"vers": "1.0.0", "deps": []},
            {"vers": "1.4.0", "deps": [
                {"name": "app", "req": "=1.0.0", "kind": "normal"}]},
            {"vers": "1.5.0", "yanked": True, "deps": []},
            {"vers": "2.0.0", "deps": []},
        ],
    }
    key = url.split("example.org/")[1]
    return "\n".join(json.dumps(item) for item in data[key])


class RegistrySourceTest(unittest.TestCase):
    """Подбор версий для реального реестра."""

    def test_resolve_and_cycle(self):
        """Берётся старшая подходящая невыдернутая версия."""
        source = RegistrySource("https://example.org", fake_index)
        self.assertEqual(source.resolve("lib", "^1"), "1.4.0")
        graph = build_graph(source.root("app", "1.0.0"),
                            source.dependencies, 5)
        self.assertEqual(list(graph.edges),
                         [("app", "1.0.0"), ("lib", "1.4.0")])
        self.assertEqual(len(find_cycles(graph)), 1)


if __name__ == "__main__":
    unittest.main()

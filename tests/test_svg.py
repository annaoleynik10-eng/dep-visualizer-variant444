"""Тесты рисования графа в SVG."""
import os
import tempfile
import unittest
import xml.etree.ElementTree as etree

from depviz.graph import build_graph, find_cycles
from depviz.sources import FileSource
from depviz.svg import cycle_edges, layout, save_svg, to_svg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOS = os.path.join(ROOT, "tests", "repos")


def graph_of(repo, root, depth):
    """Граф по тестовому репозиторию."""
    source = FileSource(os.path.join(REPOS, repo + ".txt"))
    return build_graph(root, source.dependencies, depth)


class SvgTest(unittest.TestCase):
    """Картинка графа без сторонних библиотек."""

    def test_valid_svg(self):
        """Получается правильный XML: прямоугольник и подпись на пакет."""
        graph = graph_of("simple", "A", 5)
        root = etree.fromstring(to_svg(graph, str))
        tag = "{http://www.w3.org/2000/svg}text"
        texts = [el.text for el in root.iter(tag)]
        self.assertEqual(sorted(texts), ["A", "B", "C", "D", "E"])

    def test_levels(self):
        """Пакеты одного уровня BFS стоят на одной высоте."""
        pos, _, _ = layout(graph_of("simple", "A", 5), str)
        self.assertEqual(pos["B"][1], pos["C"][1])
        self.assertLess(pos["A"][1], pos["B"][1])
        self.assertLess(pos["B"][1], pos["D"][1])

    def test_cycle_red(self):
        """Стрелки цикла рисуются красным классом b."""
        graph = graph_of("cycle", "A", 10)
        cycles = find_cycles(graph)
        self.assertIn(("C", "A"), cycle_edges(cycles))
        self.assertEqual(to_svg(graph, str, cycles).count('class="b"'), 3)
        self.assertNotIn('class="b"', to_svg(graph, str))

    def test_save(self):
        """Файл .svg сохраняется в папку."""
        with tempfile.TemporaryDirectory() as tmp:
            path = save_svg("<svg/>", "a b", tmp)
            self.assertTrue(path.endswith("a_b.svg"))
            self.assertTrue(os.path.isfile(path))


if __name__ == "__main__":
    unittest.main()

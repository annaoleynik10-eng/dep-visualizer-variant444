"""Тесты этапа 5: текст Mermaid и сохранение изображения."""
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

from depviz.__main__ import main
from depviz.graph import build_graph
from depviz.mermaid import save, to_mermaid
from depviz.sources import FileSource

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOS = os.path.join(ROOT, "tests", "repos")


def graph_of(repo, root, depth):
    """Граф по тестовому репозиторию."""
    source = FileSource(os.path.join(REPOS, repo + ".txt"))
    return build_graph(root, source.dependencies, depth)


class MermaidTest(unittest.TestCase):
    """Формирование диаграммы."""

    def test_text(self):
        """Вершины, рёбра и выделение корня."""
        text = to_mermaid(graph_of("simple", "A", 5), str)
        lines = text.splitlines()
        self.assertEqual(lines[0], "graph TD")
        self.assertIn('    n0["A"]', lines)
        self.assertIn("    n0 --> n1", lines)
        self.assertIn("    n2 --> n3", lines)
        self.assertIn("    class n0 root", lines)
        self.assertEqual(text.count("-->"), 5)

    def test_cut_and_cycle(self):
        """Обрезанные по глубине вершины и цикл."""
        self.assertIn("class n2 cut", to_mermaid(graph_of("chain", "A", 2),
                                                 str))
        self.assertIn("n2 --> n0", to_mermaid(graph_of("cycle", "A", 9),
                                              str))

    def test_save(self):
        """Сохраняются .mmd и .html с подключённым Mermaid."""
        with tempfile.TemporaryDirectory() as tmp:
            page = save("graph TD\n    n0[\"A\"]", "x y", tmp)
            self.assertTrue(page.endswith("x_y.html"))
            self.assertTrue(os.path.isfile(os.path.join(tmp, "x_y.mmd")))
            with open(page, encoding="utf-8") as file:
                html = file.read()
            self.assertIn('class="mermaid"', html)
            self.assertIn("mermaid.min.js", html)

    def test_main_mermaid(self):
        """Режим mermaid: текст на экран, браузер открывается."""
        out = io.StringIO()
        config = os.path.join(ROOT, "configs", "mermaid_test_complex.ini")
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(out), \
                mock.patch("webbrowser.open", return_value=True) as browser:
            old = os.getcwd()
            os.chdir(tmp)
            try:
                code = main([config])
            finally:
                os.chdir(old)
        self.assertEqual(code, 0)
        self.assertTrue(browser.called)
        self.assertIn("graph TD", out.getvalue())
        self.assertIn("image: out/A.html", out.getvalue())
        self.assertIn("picture: out/A.svg", out.getvalue())


if __name__ == "__main__":
    unittest.main()

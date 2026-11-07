"""Текстовое представление графа на языке Mermaid и показ картинки.

Картинку рисует сама библиотека Mermaid в браузере: программа
сохраняет HTML-страницу с текстом диаграммы и открывает её модулем
webbrowser из стандартной библиотеки.
"""
import html
import os
import re
import webbrowser
from pathlib import Path

MERMAID_JS = "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"
SAFE_NAME = re.compile(r"[^A-Za-z0-9_.-]")
PAGE = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
body {{ font-family: sans-serif; margin: 24px; background: #fff; }}
pre.src {{ background: #f4f6fa; padding: 12px; overflow-x: auto; }}
</style>
</head>
<body>
<h2>{title}</h2>
<pre class="mermaid">
{diagram}
</pre>
<details><summary>Текст диаграммы Mermaid</summary>
<pre class="src">{diagram}</pre></details>
<script src="{script}"></script>
<script>mermaid.initialize({{ startOnLoad: true }});</script>
</body>
</html>
"""


def node_ids(graph):
    """Короткие идентификаторы вершин: n0, n1, ... в порядке обхода."""
    return {node: f"n{index}" for index, node in enumerate(graph.edges)}


def to_mermaid(graph, label):
    """Сформировать текст диаграммы Mermaid для графа зависимостей."""
    ids = node_ids(graph)
    lines = ["graph TD"]
    for node, node_id in ids.items():
        text = label(node).replace('"', "'")
        lines.append(f'    {node_id}["{text}"]')
    for node, children in graph.edges.items():
        for child in children:
            lines.append(f"    {ids[node]} --> {ids[child]}")
    lines.append("    classDef root fill:#ffe9a8,stroke:#b7791f")
    lines.append("    classDef cut stroke-dasharray:5 5")
    lines.append(f"    class {ids[graph.root]} root")
    if graph.cut:
        cut = ",".join(ids[node] for node in graph.cut)
        lines.append(f"    class {cut} cut")
    return "\n".join(lines)


def save(diagram, title, out_dir):
    """Сохранить .mmd (текст) и .html (картинка); вернуть путь к HTML."""
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, SAFE_NAME.sub("_", title))
    with open(base + ".mmd", "w", encoding="utf-8") as file:
        file.write(diagram + "\n")
    page = PAGE.format(title=html.escape(title), diagram=html.escape(diagram),
                       script=MERMAID_JS)
    with open(base + ".html", "w", encoding="utf-8") as file:
        file.write(page)
    return base + ".html"


def show(path):
    """Открыть HTML-страницу с изображением графа в браузере."""
    return webbrowser.open(Path(path).resolve().as_uri())

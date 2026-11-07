"""Рисование графа в файл SVG без сторонних библиотек.

SVG — это картинка, записанная текстом (как HTML). Её можно открыть
в VS Code, в браузере или вставить в README. Пакеты раскладываются
по уровням: строка = глубина из обхода BFS.
"""
import html
import os
import re

BOX_HEIGHT = 44
CHAR_WIDTH = 9
BOX_PADDING = 28
GAP_X = 40
GAP_Y = 90
BEND = 0.55
MARGIN = 40
SAFE_NAME = re.compile(r"[^A-Za-z0-9_.-]")
ROOT_FILL = "#ffe9a8"
NODE_FILL = "#eef0ff"
CUT_DASH = "6 4"
STYLE = ('<style>text{font-family:sans-serif;font-size:15px}'
         '.e{stroke:#8a93a6;stroke-width:1.6;fill:none}'
         '.b{stroke:#d64545;stroke-width:1.6;fill:none}</style>')
MARKERS = ('<defs>'
           '<marker id="a" viewBox="0 0 10 10" refX="10" refY="5" '
           'markerWidth="8" markerHeight="8" orient="auto">'
           '<path d="M0,0L10,5L0,10z" fill="#8a93a6"/></marker>'
           '<marker id="r" viewBox="0 0 10 10" refX="10" refY="5" '
           'markerWidth="8" markerHeight="8" orient="auto">'
           '<path d="M0,0L10,5L0,10z" fill="#d64545"/></marker></defs>')


def box_width(text):
    """Ширина прямоугольника под подпись."""
    return len(text) * CHAR_WIDTH + BOX_PADDING


def layout(graph, label):
    """Координаты центра каждого пакета: уровень — по глубине BFS."""
    rows = {}
    for node in graph.edges:
        rows.setdefault(graph.depth[node], []).append(node)
    widths = {depth: sum(box_width(label(n)) + GAP_X for n in nodes) - GAP_X
              for depth, nodes in rows.items()}
    page = max(widths.values()) + 2 * MARGIN
    pos = {}
    for depth, nodes in rows.items():
        x = (page - widths[depth]) / 2
        y = MARGIN + depth * (BOX_HEIGHT + GAP_Y) + BOX_HEIGHT / 2
        for node in nodes:
            width = box_width(label(node))
            pos[node] = (x + width / 2, y)
            x += width + GAP_X
    height = MARGIN * 2 + len(rows) * (BOX_HEIGHT + GAP_Y) - GAP_Y
    return pos, page, height


def edge(start, end, in_cycle):
    """Стрелка между пакетами; стрелки цикла — красные.

    Вниз — прямая линия; на том же уровне — дуга под пакетами;
    вверх — плавная S-кривая от верха пакета к низу зависимости.
    """
    (x1, y1), (x2, y2) = start, end
    half = BOX_HEIGHT / 2
    kind, marker = ("b", "r") if in_cycle else ("e", "a")
    tail = f'class="{kind}" marker-end="url(#{marker})"/>'
    if y2 > y1:
        return (f'<line x1="{x1:.0f}" y1="{y1 + half:.0f}" x2="{x2:.0f}" '
                f'y2="{y2 - half:.0f}" {tail}')
    if y2 == y1:
        low = y1 + half + GAP_Y * BEND
        return (f'<path d="M{x1:.0f},{y1 + half:.0f} C{x1:.0f},{low:.0f} '
                f'{x2:.0f},{low:.0f} {x2:.0f},{y2 + half:.0f}" {tail}')
    return (f'<path d="M{x1:.0f},{y1 - half:.0f} C{x1:.0f},'
            f'{y1 - GAP_Y:.0f} {x2:.0f},{y2 + GAP_Y:.0f} {x2:.0f},'
            f'{y2 + half:.0f}" {tail}')


def node_box(node, center, label, graph):
    """Прямоугольник с подписью пакета."""
    text = label(node)
    width = box_width(text)
    x, y = center
    fill = ROOT_FILL if node == graph.root else NODE_FILL
    dash = f' stroke-dasharray="{CUT_DASH}"' if node in graph.cut else ""
    return (f'<rect x="{x - width / 2:.0f}" y="{y - BOX_HEIGHT / 2:.0f}" '
            f'width="{width}" height="{BOX_HEIGHT}" rx="10" fill="{fill}" '
            f'stroke="#6b6fd6"{dash}/>'
            f'<text x="{x:.0f}" y="{y + 5:.0f}" text-anchor="middle">'
            f'{html.escape(text)}</text>')


def cycle_edges(cycles):
    """Множество стрелок, входящих в найденные циклы."""
    return {(cycle[i], cycle[i + 1]) for cycle in cycles
            for i in range(len(cycle) - 1)}


def to_svg(graph, label, cycles=()):
    """Сформировать текст SVG-картинки; стрелки циклов — красные."""
    pos, width, height = layout(graph, label)
    red = cycle_edges(cycles)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
             f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}">',
             STYLE, MARKERS,
             '<rect width="100%" height="100%" fill="#ffffff"/>']
    for node, children in graph.edges.items():
        for child in children:
            parts.append(edge(pos[node], pos[child], (node, child) in red))
    for node, center in pos.items():
        parts.append(node_box(node, center, label, graph))
    parts.append("</svg>")
    return "\n".join(parts)


def save_svg(picture, title, out_dir):
    """Сохранить картинку в out_dir/<название>.svg и вернуть путь."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, SAFE_NAME.sub("_", title) + ".svg")
    with open(path, "w", encoding="utf-8") as file:
        file.write(picture + "\n")
    return path

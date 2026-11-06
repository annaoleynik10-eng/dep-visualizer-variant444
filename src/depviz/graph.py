"""Построение графа зависимостей обходом в ширину (BFS) без рекурсии."""
from collections import deque
from dataclasses import dataclass, field

WHITE = 0
GRAY = 1
BLACK = 2


@dataclass
class DepGraph:
    """Граф зависимостей: вершины в порядке обхода и рёбра."""

    root: object
    edges: dict = field(default_factory=dict)
    depth: dict = field(default_factory=dict)
    cut: set = field(default_factory=set)

    def edge_count(self):
        """Число рёбер графа."""
        return sum(len(children) for children in self.edges.values())


def build_graph(root, get_deps, max_depth):
    """Обойти зависимости в ширину, не глубже max_depth.

    Очередь хранит вершины, которые ещё надо раскрыть. Словарь depth
    одновременно служит множеством посещённых вершин: вершина попадает
    в очередь только один раз, поэтому циклы не приводят к зависанию.
    """
    graph = DepGraph(root, {root: []}, {root: 0})
    queue = deque([root])
    while queue:
        node = queue.popleft()
        if graph.depth[node] >= max_depth:
            graph.cut.add(node)
            continue
        for child in get_deps(node):
            graph.edges[node].append(child)
            if child not in graph.depth:
                graph.depth[child] = graph.depth[node] + 1
                graph.edges[child] = []
                queue.append(child)
    return graph


def find_cycles(graph):
    """Найти циклы обходом в глубину на явном стеке (без рекурсии).

    Цвета: WHITE — не посещена, GRAY — сейчас на пути от корня,
    BLACK — полностью обработана. Ребро в GRAY-вершину замыкает цикл.
    """
    color = {node: WHITE for node in graph.edges}
    cycles = []
    color[graph.root] = GRAY
    path = [graph.root]
    stack = [iter(graph.edges[graph.root])]
    while stack:
        child = next(stack[-1], None)
        if child is None:
            color[path.pop()] = BLACK
            stack.pop()
        elif color[child] == GRAY:
            start = path.index(child)
            cycles.append(path[start:] + [child])
        elif color[child] == WHITE:
            color[child] = GRAY
            path.append(child)
            stack.append(iter(graph.edges[child]))
    return cycles

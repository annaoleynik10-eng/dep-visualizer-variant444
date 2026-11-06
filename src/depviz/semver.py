"""Версии в формате semver и требования к версиям в стиле Cargo.

Требование (например, ^1.2, ~0.3, >=1, <2, 1.*) превращается в список
простых сравнений (оператор, версия). Версия подходит, если выполнены
все сравнения. Правила взяты из документации Cargo.
"""
import re

from depviz.errors import DepVizError

PARTS = 3
ONE_PART = 1
TWO_PARTS = 2
WILDCARDS = ("*", "x", "X")
OPERATOR = re.compile(r"^\s*(\^|~|=|>=|<=|>|<)?\s*(.*?)\s*$")
CHECKS = {
    ">=": lambda a, b: a >= b,
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    "=": lambda a, b: a == b,
}


class VersionError(DepVizError):
    """Неверная запись версии или требования."""


def parse_version(text):
    """Разобрать '1.2.3-beta+build' в кортеж для сравнения.

    Кортеж: (major, minor, patch, признак релиза, pre-release).
    Предварительная версия (1.0.0-beta) меньше релиза 1.0.0.
    """
    core = text.strip().split("+", 1)[0]
    core, _, pre = core.partition("-")
    numbers = core.split(".")
    if len(numbers) != PARTS or not all(n.isdigit() for n in numbers):
        raise VersionError(f"bad version: {text}")
    major, minor, patch = (int(n) for n in numbers)
    return (major, minor, patch, 0 if pre else 1, pre)


def split_partial(body):
    """'1.2' -> ([1, 2], 2); части после * отбрасываются."""
    numbers = []
    for part in body.split("."):
        if part in WILDCARDS:
            break
        if not part.isdigit():
            raise VersionError(f"bad version requirement: {body}")
        numbers.append(int(part))
    count = len(numbers)
    return numbers + [0] * (PARTS - count), count


def caret_upper(numbers, count):
    """Верхняя граница для ^: не меняется первая ненулевая часть."""
    major, minor, patch = numbers
    if major or count == ONE_PART:
        return (major + 1, 0, 0)
    if minor or count == TWO_PARTS:
        return (0, minor + 1, 0)
    return (0, 0, patch + 1)


def tilde_upper(numbers, count):
    """Верхняя граница для ~: меняется только patch."""
    major, minor, _ = numbers
    if count == ONE_PART:
        return (major + 1, 0, 0)
    return (major, minor + 1, 0)


def release(numbers):
    """Кортеж версии-релиза из трёх чисел."""
    return (numbers[0], numbers[1], numbers[2], 1, "")


def lowest(numbers):
    """Самая маленькая версия с этими числами (меньше любых pre-release)."""
    return (numbers[0], numbers[1], numbers[2], 0, "")


def normalize_operator(op, body, count):
    """Оператор для неполной версии: 1.2 -> ^, =1.2 и 1.2.* -> ~."""
    if count == PARTS or op not in (None, "="):
        return op or "^"
    if op == "=" or body[-1] in WILDCARDS:
        return "~"
    return "^"


def range_rules(op, numbers, count):
    """Сравнения для ^ и ~: нижняя и верхняя граница."""
    upper = caret_upper(numbers, count) if op == "^" else \
        tilde_upper(numbers, count)
    return [(">=", release(numbers)), ("<", lowest(upper))]


def parse_comparator(text):
    """Разобрать одно сравнение и вернуть список (оператор, версия)."""
    op, body = OPERATOR.match(text).groups()
    if body in WILDCARDS or not body:
        return []
    if "-" in body:
        return [(op if op and op != "^" else ">=", parse_version(body))]
    numbers, count = split_partial(body)
    if not count:
        return []
    op = normalize_operator(op, body, count)
    if op in ("^", "~"):
        return range_rules(op, numbers, count)
    return [(op, release(numbers))]


def parse_requirement(text):
    """Разобрать требование 'a, b, c' в общий список сравнений."""
    rules = []
    for part in text.split(","):
        rules.extend(parse_comparator(part))
    return rules


def allows_prerelease(version, rules):
    """Pre-release подходит, только если в требовании та же x.y.z-pre."""
    return any(rule[1][:PARTS] == version[:PARTS] and rule[1][PARTS + 1]
               for rule in rules)


def matches(version, rules):
    """Проверить, удовлетворяет ли версия всем сравнениям."""
    if version[PARTS + 1] and not allows_prerelease(version, rules):
        return False
    return all(CHECKS[op](version, bound) for op, bound in rules)

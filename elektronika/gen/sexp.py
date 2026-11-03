"""Минимальный разбор/запись s-выражений KiCad."""
import re

_tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)


class Sym(str):
    """Атом без кавычек (ключевое слово, число)."""


def parse(text):
    stack, cur = [], []
    pos = 0
    n = len(text)
    while pos < n:
        m = _tok.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise ValueError("разбор: %r" % text[pos:pos + 40])
        pos = m.end()
        if m.group(1):
            stack.append(cur)
            cur = []
        elif m.group(2):
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif m.group(3) is not None:
            cur.append(re.sub(r'\\(.)', lambda k: {"n": "\n"}.get(k.group(1), k.group(1)), m.group(3)))
        else:
            cur.append(Sym(m.group(4)))
    return cur[0] if len(cur) == 1 else cur


def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def find1(node, key):
    r = find(node, key)
    return r[0] if r else None


def dump(node, ind=0):
    if isinstance(node, list):
        inner = [dump(c, ind + 1) for c in node]
        one = "(" + " ".join(inner) + ")"
        if len(one) < 100 and "\n" not in one:
            return one
        return "(" + inner[0] + "".join("\n" + "  " * (ind + 1) + s for s in inner[1:]) + ")"
    if isinstance(node, Sym):
        return str(node)
    if isinstance(node, bool):
        return "yes" if node else "no"
    if isinstance(node, (int, float)):
        s = ("%.4f" % node).rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    return '"' + str(node).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'

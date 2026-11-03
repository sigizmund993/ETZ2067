"""Символы из стандартной библиотеки KiCad: загрузка, «расплющивание»
производных (extends) и координаты выводов."""
import math, os, copy
import sexp
from sexp import Sym, find, find1

SYM_DIR = os.environ.get("KICAD_SYM_DIR", "/usr/share/kicad/symbols")
_cache = {}


def _lib_symbols(lib):
    if lib in _cache:
        return _cache[lib]
    out = {}
    f = os.path.join(SYM_DIR, lib + ".kicad_sym")
    files = [f] if os.path.exists(f) else []
    d = os.path.join(SYM_DIR, lib + ".kicad_symdir")
    if os.path.isdir(d):
        files += [os.path.join(d, n) for n in sorted(os.listdir(d)) if n.endswith(".kicad_sym")]
    for p in files:
        t = sexp.parse(open(p, encoding="utf-8").read())
        for s in find(t, "symbol"):
            out[s[1]] = s
    _cache[lib] = out
    return out


def load(lib_id):
    """Готовый к вставке в lib_symbols схемы символ 'Lib:Name' (без extends)."""
    lib, name = lib_id.split(":")
    syms = _lib_symbols(lib)
    s = copy.deepcopy(syms[name])
    ext = find1(s, "extends")
    if ext:
        parent = load(lib + ":" + ext[1])
        pname = parent[1].split(":")[1]
        own = {p[1]: p for p in find(s, "property")}
        res = [Sym("symbol"), lib_id]
        for c in parent[2:]:
            if isinstance(c, list) and c and c[0] == "property" and c[1] in own:
                res.append(own.pop(c[1]))
            elif isinstance(c, list) and c and c[0] == "symbol":
                cc = copy.deepcopy(c)
                cc[1] = name + cc[1][len(pname):]
                res.append(cc)
            else:
                res.append(c)
        # собственные свойства, которых нет у родителя — перед юнитами
        idx = next(i for i, c in enumerate(res) if isinstance(c, list) and c and c[0] == "symbol")
        for p in own.values():
            res.insert(idx, p)
            idx += 1
        return res
    s[1] = lib_id
    return s


def pins(symbol, unit=1):
    """{номер: (x, y, угол, имя, тип)} в координатах библиотеки (Y вверх)."""
    out = {}
    for u in find(symbol, "symbol"):
        # имя юнита Name_U_S: U = 0 — общий для всех юнитов
        parts = u[1].rsplit("_", 2)
        un = int(parts[-2])
        if un not in (0, unit):
            continue
        for p in find(u, "pin"):
            at = find1(p, "at")
            num = find1(p, "number")[1]
            nm = find1(p, "name")[1]
            out.setdefault(num, []).append((float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0,
                                            nm, str(p[1])))
    return out


def place(x, y, rot, px, py, pang):
    """Вывод символа, поставленного в (x, y) с поворотом rot: координаты
    точки подключения на листе (Y вниз) и направление наружу (градусы на листе,
    0 — вправо, 90 — вверх)."""
    a = math.radians(rot)
    rx = px * math.cos(a) - py * math.sin(a)
    ry = px * math.sin(a) + py * math.cos(a)
    out_dir = (pang + rot + 180.0) % 360.0
    return x + rx, y - ry, out_dir

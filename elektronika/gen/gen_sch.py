"""Схема Э3 (лист 1, A3) и перечень элементов ПЭ3 (листы 2...) из netlist.py.

    python3 gen_sch.py      -> ../etz_plata.kicad_sch (+ pe3.kicad_sch), ../gost_A2.kicad_wks

Линии связи — короткие отрезки от выводов с метками цепей (ГОСТ 2.702,
п. 5.1.5: обрыв линии связи с адресом). UUID детерминированы (от
обозначения), поэтому плата остаётся привязанной к схеме при пересборке.
"""
import os, uuid, math
import sexp, symlib, gost, netlist as N
from sexp import Sym

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
PROJECT = "etz_plata"
NS = uuid.UUID("6f1f1c1e-5a1e-4c3e-9e1a-2026e7a2067e")
FONT = gost.FONT

DOC = dict(
    code="ЕТЗ.467000.001 Э3",
    code_pe="ЕТЗ.467000.001 ПЭ3",
    name=["Плата приводов", "Схема электрическая", "принципиальная"],
    name_pe=["Плата приводов", "Перечень элементов"],
    org=["ВсОШ", "Робототехника"],
    signs=[("", ""), ("", ""), ("", ""), ("", ""), ("", ""), ("", "")],
)


def U(*k):
    return str(uuid.uuid5(NS, "/".join(map(str, k))))


ROOT = U("root")
PE_SHEET = U("pe3-sheet")


def S(x):
    return Sym(x)


def eff(size=2.5, justify=None, hide=False):
    e = [S("effects"), font(size)]
    if justify:
        e.append([S("justify")] + [S(j) for j in justify.split()])
    if hide:
        e.append([S("hide"), S("yes")])
    return e


def font(size):
    f = [S("font"), [S("size"), size, size]]
    if FONT:
        f.insert(1, [S("face"), FONT])
    return f


def snap(v, g=1.27):
    return round(v / g) * g


# ---------------------------------------------------------------- компоновка
# ref -> (x, y, rot); y вниз, мм. Заполняется в layout.py
from layout import SCH as LAYOUT, BLOCKS


def place_unit(items, p, sym, unit, x, y, rot, conn):
    ref = p["ref"]
    pins = symlib.pins(sym, unit)
    props = {pr[1]: pr for pr in sexp.find(sym, "property")}
    su = U("sym", ref) if unit == 1 else U("sym", ref, unit)
    inst = [S("symbol"), [S("lib_id"), p["sym"]], [S("at"), x, y, rot], [S("unit"), unit],
            [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")],
            [S("on_board"), S("yes" if p.get("on_board", True) else "no")],
            [S("dnp"), S("no")], [S("uuid"), su]]
    # 2-выводные: обозначение и номинал сбоку от оси выводов
    two = None
    if len(pins) == 2:
        pts = [symlib.place(x, y, rot, *lst[0][:3])[:2] for lst in pins.values()]
        two = "v" if abs(pts[0][0] - pts[1][0]) < 0.01 else "h"
    for key, val, hide in (("Reference", ref, False), ("Value", p["value"], False),
                           ("Footprint", p["fp"], True), ("Datasheet", "", True),
                           ("Description", "", True)):
        pr = props.get(key)
        j = None
        if two == "v" and key in ("Reference", "Value"):
            fx, fy, j = x + 2.54, y + (-0.635 if key == "Reference" else 2.54), "left"
        elif two == "h" and key in ("Reference", "Value"):
            fx, fy = x, y + (-3.81 if key == "Reference" else 3.81)
        else:
            at = sexp.find1(pr, "at") if pr else None
            px, py = (float(at[1]), float(at[2])) if at else (0, 0)
            a = math.radians(rot)
            fx = x + px * math.cos(a) - py * math.sin(a)
            fy = y - (px * math.sin(a) + py * math.cos(a))
            jj = sexp.find1(sexp.find1(pr, "effects") or [], "justify") if pr else None
            if jj:
                j = " ".join(str(v) for v in jj[1:])
        inst.append([S("property"), key, val, [S("at"), snap(fx, 0.635), snap(fy, 0.635), 0],
                     eff(2.5 if key != "Value" else 2.0, j, hide)])
    for n in pins:
        inst.append([S("pin"), n, [S("uuid"), U("pin", ref, n)]])
    inst.append([S("instances"), [S("project"), PROJECT,
                                  [S("path"), "/" + ROOT, [S("reference"), ref], [S("unit"), unit]]]])
    items.append(inst)

    # отрезки и метки
    for n, lst in pins.items():
        net = conn.get(n)
        for (px, py, pang, pname, ptype) in lst:
            ax, ay, d = symlib.place(x, y, rot, px, py, pang)
            if net is None:
                if ptype == "no_connect" or pname in ("NC",):
                    continue
                items.append([S("no_connect"), [S("at"), ax, ay], [S("uuid"), U("nc", ref, n, px, py)]])
                continue
            L = 2.54
            ex = ax + L * math.cos(math.radians(d))
            ey = ay - L * math.sin(math.radians(d))
            ex, ey = round(ex, 4), round(ey, 4)
            items.append([S("wire"), [S("pts"), [S("xy"), ax, ay], [S("xy"), ex, ey]],
                          [S("stroke"), [S("width"), 0], [S("type"), S("default")]],
                          [S("uuid"), U("w", ref, n, px, py)]])
            dd = round(d) % 360
            ang, just = (180, "right bottom") if dd == 180 else (0, "left bottom")
            if dd == 90:
                ang, just = 90, "left bottom"
            elif dd == 270:
                ang, just = 270, "right bottom"
            items.append([S("label"), net, [S("at"), ex, ey, ang],
                          [S("effects"), font(1.8),
                           [S("justify")] + [S(v) for v in just.split()]],
                          [S("uuid"), U("lbl", ref, n, px, py)]])


def build_main():
    items = []
    libs = {}
    by_ref = {p["ref"]: p for p in N.PARTS}
    netpins = {}
    for p in N.PARTS:
        if p["sym"].startswith("Mechanical:"):
            continue
        for pin, net in p["pins"].items():
            netpins.setdefault(net, []).append((p["ref"], pin))

    for p in N.PARTS:
        ref = p["ref"]
        if p["sym"].startswith("Mechanical:"):
            continue          # крепёжные отверстия — только на плате
        sym = libs.get(p["sym"]) or symlib.load(p["sym"])
        libs[p["sym"]] = sym
        allpins = symlib.pins(sym, None)
        # выводы по имени -> номер
        conn = {}
        for k, net in p["pins"].items():
            if isinstance(k, str) and not k.isdigit():
                nums = [n for n, lst in allpins.items() if any(t[3] == k for t in lst)]
                if not nums:
                    raise KeyError("%s: нет вывода %s" % (ref, k))
                for n in nums:
                    conn[n] = net
            else:
                conn[str(k)] = net
        lay = LAYOUT[ref]
        units = lay if isinstance(lay, list) else [(1,) + tuple(lay)]
        for unit, x, y, rot in units:
            place_unit(items, p, sym, unit, x, y, rot, conn)

    # функциональные группы: штриховой контур и название (ГОСТ 2.702, п. 5.1.8)
    for title, x1, y1, x2, y2 in BLOCKS:
        items.append([S("rectangle"), [S("start"), x1, y1], [S("end"), x2, y2],
                      [S("stroke"), [S("width"), 0.25], [S("type"), S("dash")]],
                      [S("fill"), [S("type"), S("none")]], [S("uuid"), U("blk", title)]])
        items.append([S("text"), title, [S("exclude_from_sim"), S("no")], [S("at"), x1 + 2, y1 + 4, 0],
                      eff(3.0, "left bottom"), [S("uuid"), U("blkt", title)]])

    # лист ПЭ3 — вложенный, отдельным файлом
    items.append([S("sheet"), [S("at"), 30.48, 375.92], [S("size"), 30.48, 12.7],
                  [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
                  [S("dnp"), S("no")], [S("fields_autoplaced"), S("yes")],
                  [S("stroke"), [S("width"), 0.1524], [S("type"), S("solid")]],
                  [S("fill"), [S("color"), 0, 0, 0, 0.0]], [S("uuid"), PE_SHEET],
                  [S("property"), "Sheetname", "Перечень элементов", [S("at"), 30.48, 375.1, 0],
                   eff(2.0, "left bottom")],
                  [S("property"), "Sheetfile", "pe3.kicad_sch", [S("at"), 30.48, 389.2, 0],
                   eff(1.5, "left top")],
                  [S("instances"), [S("project"), PROJECT, [S("path"), "/" + ROOT, [S("page"), "2"]]]]])

    tb = [S("title_block"), [S("title"), DOC["name"][0]], [S("date"), ""], [S("company"), DOC["org"][0]],
          [S("comment"), 1, DOC["code"]]]
    sch = [S("kicad_sch"), [S("version"), 20250114], [S("generator"), "eeschema"],
           [S("generator_version"), "9.0"], [S("uuid"), ROOT], [S("paper"), "A2"], tb,
           [S("lib_symbols")] + list(libs.values())] + items + \
          [[S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]], [S("embedded_fonts"), S("no")]]
    open(os.path.join(OUT, PROJECT + ".kicad_sch"), "w", encoding="utf-8").write(sexp.dump(sch) + "\n")
    return netpins


# ---------------------------------------------------------------- ПЭ3
GROUPS = [("A", "Модули"), ("C", "Конденсаторы"), ("DA", "Микросхемы аналоговые"),
          ("DD", "Микросхемы цифровые"), ("FU", "Предохранители"),
          ("HL", "Индикаторы"), ("L", "Дроссели"), ("R", "Резисторы"), ("SB", "Кнопки"), ("VD", "Диоды"),
          ("VT", "Транзисторы"), ("X", "Соединители"), ("XS", "Розетки")]


def _prefix(ref):
    return "".join(ch for ch in ref if ch.isalpha())


def _num(ref):
    return int("".join(ch for ch in ref if ch.isdigit()))


def pe3_rows():
    rows = []
    parts = [p for p in N.PARTS if not p["sym"].startswith("Mechanical:")]
    for pre, gname in GROUPS:
        grp = sorted([p for p in parts if _prefix(p["ref"]) == pre], key=lambda p: _num(p["ref"]))
        if not grp:
            continue
        rows.append(("", gname, "", ""))
        # подряд идущие одинаковые — одной строкой (ГОСТ 2.701, п. 5.6.4)
        i = 0
        while i < len(grp):
            j = i
            while (j + 1 < len(grp) and grp[j + 1]["name"] == grp[i]["name"]
                   and grp[j + 1].get("note", "") == grp[i].get("note", "")
                   and _num(grp[j + 1]["ref"]) == _num(grp[j]["ref"]) + 1):
                j += 1
            a, b = grp[i]["ref"], grp[j]["ref"]
            pos = a if i == j else (a + ", " + b if j == i + 1 else a + "…" + b)
            rows.append((pos, grp[i]["name"], str(j - i + 1), grp[i].get("note", "")))
            i = j + 1
        rows.append(("", "", "", ""))
    return rows


def _wrap(s, n):
    words, out, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        out.append(cur)
    return out or [""]


def build_pe3():
    W, H = 210, 297
    rows = []
    for pos, nm, q, note in pe3_rows():
        nl = _wrap(nm, 44)
        tl = _wrap(note, 18)
        for k in range(max(len(nl), len(tl))):
            rows.append((pos if k == 0 else "", nl[k] if k < len(nl) else "",
                         q if k == 0 else "", tl[k] if k < len(tl) else ""))
    while rows and rows[-1] == ("", "", "", ""):
        rows.pop()
    pages = []
    first, other = (H - 5 - 40 - 20) // 8, (H - 5 - 15 - 20) // 8
    i = 0
    while i < len(rows):
        n = first if not pages else other
        pages.append(rows[i:i + n])
        i += n
    total = len(pages)
    items = []
    for pg, prow in enumerate(pages):
        # страницы ПЭ3 лежат одна под другой на одном листе A4? нет — каждая — свой лист:
        pass
    return pages, total


def pe3_sheet_items(prow, pg, total, sh):
    gost.frame(sh)
    if pg == 0:
        gost.form2(sh, dict(code=DOC["code_pe"], name=DOC["name_pe"], org=DOC["org"],
                            list="", listov=str(total), signs=DOC["signs"]))
    else:
        gost.form2a(sh, dict(code=DOC["code_pe"], list=str(pg + 1)))
    gost.extra_graphs(sh, DOC["code_pe"] if pg == 0 else "", graph26=False)
    # таблица: 20 | 110 | 10 | 45, шапка 15, строки 8
    X0, Y0 = 20, 5
    cols = (20, 110, 10, 45)
    bottom = sh.h - 5 - (40 if pg == 0 else 15)
    xs = [X0]
    for c in cols:
        xs.append(xs[-1] + c)
    for x in xs[1:-1]:
        sh.line(x, Y0, x, bottom, gost.THICK)
    sh.line(X0, Y0 + 15, X0 + 185, Y0 + 15, gost.THICK)
    y = Y0 + 15
    while y + 8 <= bottom + 0.01:
        y += 8
        sh.line(X0, y, X0 + 185, y, gost.THIN)
    for x1, x2, t in zip(xs, xs[1:], ("Поз.\nобозна-\nчение", "Наименование", "Кол.", "Примечание")):
        ls = t.split("\n")
        for k, s in enumerate(ls):
            sh.text((x1 + x2) / 2, Y0 + 7.5 + (k - (len(ls) - 1) / 2) * 3.5, s, 2.5)
    for r, (pos, nm, q, note) in enumerate(prow):
        yc = Y0 + 15 + 8 * r + 4
        if pos:
            sh.text(xs[0] + 1.5, yc, pos, 2.5, "left")
        if nm:
            if not pos and not q:
                sh.text((xs[1] + xs[2]) / 2, yc, nm, 3.0)       # заголовок группы — по центру
            else:
                sh.text(xs[1] + 1.5, yc, nm, 2.5, "left")
        if q:
            sh.text((xs[2] + xs[3]) / 2, yc, q, 2.5)
        if note:
            sh.text(xs[3] + 1.5, yc, note, 2.5, "left")


def sheet_graphics(sh, tag):
    """Линии и тексты Sheet -> элементы kicad_sch."""
    out = []
    for i, (x1, y1, x2, y2, wd) in enumerate(sh.lines):
        out.append([S("polyline"), [S("pts"), [S("xy"), x1, y1], [S("xy"), x2, y2]],
                    [S("stroke"), [S("width"), wd], [S("type"), S("solid")]],
                    [S("uuid"), U(tag, "l", i)]])
    for i, (x, y, s, size, just, ang) in enumerate(sh.texts):
        j = {"left": "left", "center": None, "right": "right"}[just]
        out.append([S("text"), s, [S("exclude_from_sim"), S("no")], [S("at"), x, y, ang],
                    eff(size, j), [S("uuid"), U(tag, "t", i)]])
    return out


def write_pe3():
    pages, total = build_pe3()
    import glob
    for old in glob.glob(os.path.join(OUT, "pe3_*.kicad_sch")):
        os.remove(old)
    # один вложенный лист A4 на страницу ПЭ3: pe3.kicad_sch — первая, pe3_2... — следующие
    # Для простоты: все страницы ПЭ3 — в одном файле нельзя (KiCad: один файл = один лист),
    # поэтому первая страница — pe3.kicad_sch, следующие — вложенные в неё листы.
    files = []
    for pg, prow in enumerate(pages):
        sh = gost.Sheet(210, 297)
        pe3_sheet_items(prow, pg, total, sh)
        items = sheet_graphics(sh, "pe%d" % pg)
        fname = "pe3.kicad_sch" if pg == 0 else "pe3_%d.kicad_sch" % (pg + 1)
        files.append((fname, items))
    for k, (fname, items) in enumerate(files):
        su = U("pe3file", k)
        extra = []
        if k + 1 < len(files):
            nxt = files[k + 1][0]
            extra.append([S("sheet"), [S("at"), 150, 300], [S("size"), 20, 5],
                          [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
                          [S("dnp"), S("no")],
                          [S("stroke"), [S("width"), 0.1], [S("type"), S("solid")]],
                          [S("fill"), [S("color"), 0, 0, 0, 0.0]], [S("uuid"), U("pe3sheet", k + 1)],
                          [S("property"), "Sheetname", "ПЭ3 лист %d" % (k + 2), [S("at"), 150, 299.5, 0],
                           eff(1.5, "left bottom")],
                          [S("property"), "Sheetfile", nxt, [S("at"), 150, 305.6, 0], eff(1.5, "left top")],
                          [S("instances"), [S("project"), PROJECT,
                                            [S("path"), "/" + ROOT + "/" + PE_SHEET +
                                             "".join("/" + U("pe3sheet", m) for m in range(1, k + 1)),
                                             [S("page"), str(k + 3)]]]]])
        sch = [S("kicad_sch"), [S("version"), 20250114], [S("generator"), "eeschema"],
               [S("generator_version"), "9.0"], [S("uuid"), su], [S("paper"), "A4", S("portrait")],
               [S("lib_symbols")]] + items + extra + [[S("embedded_fonts"), S("no")]]
        open(os.path.join(OUT, fname), "w", encoding="utf-8").write(sexp.dump(sch) + "\n")
    return len(files)


def write_wks():
    sh = gost.Sheet(594, 420)
    gost.frame(sh)
    gost.form1(sh, dict(code="${COMMENT1}", name=DOC["name"], org=DOC["org"], listov="1",
                        signs=DOC["signs"]))
    gost.extra_graphs(sh, "${COMMENT1}")
    gost.to_wks(sh, os.path.join(OUT, "gost_A2.kicad_wks"), page1only=True)


if __name__ == "__main__":
    write_wks()
    netpins = build_main()
    n = write_pe3()
    print("Э3 + ПЭ3: %d лист(ов) перечня; цепей %d" % (n, len(netpins)))

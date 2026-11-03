"""Рамка и основные надписи ГОСТ 2.104 (форма 1 — чертежи и схемы, 2 и 2а —
текстовые документы) и дополнительные графы.

Всё строится в координатах листа (мм, X вправо, Y вниз), а выводится двумя
способами: в оформление листа KiCad (.kicad_wks, первый лист схемы — там
поля берутся из основной надписи документа: ${TITLE}, ${COMMENT1}...) и
графикой прямо на листе схемы (листы перечня элементов).
"""

FONT = ""          # встроенный штриховой шрифт KiCad (в osifont сломана «Э»)
THICK, THIN = 0.5, 0.25       # основная и тонкая линии рамки


class Sheet:
    """Набор линий и надписей; потом пишется в wks или в kicad_sch."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.lines = []          # (x1, y1, x2, y2, width)
        self.texts = []          # (x, y, text, size, justify, angle)

    def line(self, x1, y1, x2, y2, wd=THIN):
        self.lines.append((x1, y1, x2, y2, wd))

    def rect(self, x1, y1, x2, y2, wd=THICK):
        for a in ((x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)):
            self.line(*a, wd)

    def text(self, x, y, s, size=2.5, justify="center", angle=0):
        self.texts.append((x, y, s, size, justify, angle))


def frame(sh):
    """Рамка: поле 20 мм слева, 5 мм с остальных сторон."""
    sh.rect(20, 5, sh.w - 5, sh.h - 5, THICK)


def _left_part(sh, X0, Y0, rows_change, sign_labels, sign_vals=None, thick_rows=()):
    """Левая часть основной надписи (графы 10-18): строки изменений, строка
    заголовков и подписи. X0, Y0 — левый верхний угол надписи."""
    cols = (7, 10, 23, 15, 10)
    xs = [X0]
    for c in cols:
        xs.append(xs[-1] + c)
    n = rows_change + 1 + len(sign_labels)
    for i in range(1, n):
        y = Y0 + 5 * i
        wd = THICK if i in thick_rows else THIN
        sh.line(X0, y, X0 + 65, y, wd)
    ych = Y0 + 5 * (rows_change + 1)          # низ строки заголовков
    for k, x in enumerate(xs[1:5]):
        y_end = ych if k == 0 else Y0 + 5 * n       # граница 7 мм — только в изменениях
        sh.line(x, Y0, x, y_end, THICK)
    sh.line(xs[5], Y0, xs[5], Y0 + 5 * n, THICK)
    yh = ych - 2.5
    for x, t in zip(xs, ("Изм.", "Лист", "N докум.", "Подп.", "Дата")):
        pass
    for k, t in enumerate(("Изм.", "Лист", "N докум.", "Подп.", "Дата")):
        sh.text((xs[k] + xs[k + 1]) / 2, yh, t, 2.5)
    for i, t in enumerate(sign_labels):
        y = ych + 5 * i + 2.5
        sh.text(X0 + 1, y, t, 2.5, "left")
        if sign_vals and sign_vals[i]:
            sh.text(xs[2] + 1, y, sign_vals[i][0], 2.5, "left")
            if len(sign_vals[i]) > 1:
                sh.text((xs[4] + xs[5]) / 2, y, sign_vals[i][1], 2.0)


def form1(sh, f):
    """Форма 1 (185 x 55) в правом нижнем углу. f — словарь значений."""
    X0, Y0 = sh.w - 5 - 185, sh.h - 5 - 55
    sh.rect(X0, Y0, X0 + 185, Y0 + 55, THICK)
    _left_part(sh, X0, Y0, 4, ("Разраб.", "Пров.", "Т.контр.", "", "Н.контр.", "Утв."),
               f.get("signs"), thick_rows=(5,))
    xm, xr = X0 + 65, X0 + 135
    sh.line(xm, Y0 + 15, X0 + 185, Y0 + 15, THICK)          # под обозначением
    sh.line(xm, Y0 + 40, X0 + 185, Y0 + 40, THICK)          # над материалом
    sh.line(xr, Y0 + 15, xr, Y0 + 55, THICK)
    sh.line(xr, Y0 + 20, X0 + 185, Y0 + 20, THICK)          # под «Лит. Масса Масштаб»
    sh.line(xr, Y0 + 35, X0 + 185, Y0 + 35, THICK)          # над «Лист Листов»
    for x in (xr + 5, xr + 10):
        sh.line(x, Y0 + 20, x, Y0 + 35, THIN)
    for x in (xr + 15, xr + 32):
        sh.line(x, Y0 + 15, x, Y0 + 35, THICK)
    sh.line(xr + 20, Y0 + 35, xr + 20, Y0 + 40, THIN)
    sh.text(xr + 7.5, Y0 + 17.5, "Лит.")
    sh.text(xr + 23.5, Y0 + 17.5, "Масса")
    sh.text(xr + 41, Y0 + 17.5, "Масштаб")
    sh.text(xr + 1, Y0 + 37.5, "Лист " + f.get("list", ""), 2.5, "left")
    sh.text(xr + 21, Y0 + 37.5, "Листов " + f.get("listov", ""), 2.5, "left")
    sh.text(xm + 60, Y0 + 7.5, f.get("code", ""), 6)
    name = f.get("name", [])
    for i, s in enumerate(name):
        sh.text(xm + 35, Y0 + 27.5 + (i - (len(name) - 1) / 2) * 6, s, 4 if i == 0 else 3.5)
    if f.get("lit"):
        sh.text(xr + 2.5, Y0 + 27.5, f["lit"], 3.5)
    if f.get("scale"):
        sh.text(xr + 41, Y0 + 27.5, f["scale"], 3.5)
    for i, s in enumerate(f.get("org", [])):
        sh.text(xr + 25, Y0 + 47.5 + (i - (len(f["org"]) - 1) / 2) * 4.5, s, 3.5)


def form2(sh, f):
    """Форма 2 (185 x 40) — первый лист текстового документа (перечень)."""
    X0, Y0 = sh.w - 5 - 185, sh.h - 5 - 40
    sh.rect(X0, Y0, X0 + 185, Y0 + 40, THICK)
    _left_part(sh, X0, Y0, 2, ("Разраб.", "Пров.", "", "Н.контр.", "Утв."),
               f.get("signs"), thick_rows=(3,))
    xm, xr = X0 + 65, X0 + 135
    sh.line(xm, Y0 + 15, X0 + 185, Y0 + 15, THICK)
    sh.line(xr, Y0 + 15, xr, Y0 + 40, THICK)
    sh.line(xr, Y0 + 20, X0 + 185, Y0 + 20, THICK)
    sh.line(xr, Y0 + 25, X0 + 185, Y0 + 25, THICK)
    for x in (xr + 5, xr + 10):
        sh.line(x, Y0 + 20, x, Y0 + 25, THIN)
    for x in (xr + 15, xr + 30):
        sh.line(x, Y0 + 15, x, Y0 + 25, THICK)
    sh.text(xr + 7.5, Y0 + 17.5, "Лит.")
    sh.text(xr + 22.5, Y0 + 17.5, "Лист")
    sh.text(xr + 40, Y0 + 17.5, "Листов")
    sh.text(xr + 22.5, Y0 + 22.5, f.get("list", ""))
    sh.text(xr + 40, Y0 + 22.5, f.get("listov", ""))
    if f.get("lit"):
        sh.text(xr + 2.5, Y0 + 22.5, f["lit"])
    sh.text(xm + 60, Y0 + 7.5, f.get("code", ""), 6)
    name = f.get("name", [])
    for i, s in enumerate(name):
        sh.text(xm + 35, Y0 + 27.5 + (i - (len(name) - 1) / 2) * 6, s, 4 if i == 0 else 3.5)
    for i, s in enumerate(f.get("org", [])):
        sh.text(xr + 25, Y0 + 32.5 + (i - (len(f["org"]) - 1) / 2) * 4.5, s, 3.5)


def form2a(sh, f):
    """Форма 2а (185 x 15) — последующие листы."""
    X0, Y0 = sh.w - 5 - 185, sh.h - 5 - 15
    sh.rect(X0, Y0, X0 + 185, Y0 + 15, THICK)
    xs = [X0 + v for v in (7, 17, 40, 55, 65)]
    for x in xs:
        sh.line(x, Y0, x, Y0 + 15, THICK)
    for i in (1, 2):
        sh.line(X0, Y0 + 5 * i, X0 + 65, Y0 + 5 * i, THICK if i == 2 else THIN)
    sh.line(X0 + 175, Y0, X0 + 175, Y0 + 15, THICK)
    sh.line(X0 + 175, Y0 + 7, X0 + 185, Y0 + 7, THIN)
    xx = [X0] + xs
    for k, t in enumerate(("Изм.", "Лист", "N докум.", "Подп.", "Дата")):
        sh.text((xx[k] + xx[k + 1]) / 2, Y0 + 12.5, t)
    sh.text(X0 + 180, Y0 + 3.5, "Лист")
    sh.text(X0 + 180, Y0 + 11, f.get("list", ""), 3.5)
    sh.text(X0 + 120, Y0 + 7.5, f.get("code", ""), 6)


def extra_graphs(sh, code="", graph26=True):
    """Дополнительные графы 19-23 (слева внизу) и 24-26 (слева вверху)."""
    x1, x2, x3 = 8, 13, 20
    heights = (("Инв. N подл.", 25), ("Подп. и дата", 35), ("Взам. инв. N", 25),
               ("Инв. N дубл.", 25), ("Подп. и дата", 35))
    y = sh.h - 5
    ys = [y]
    for _, hgt in heights:
        ys.append(ys[-1] - hgt)
    sh.line(x1, ys[0], x3, ys[0], THICK)
    for yy in ys[1:]:
        sh.line(x1, yy, x3, yy, THICK)
    sh.line(x1, ys[0], x1, ys[-1], THICK)
    sh.line(x2, ys[0], x2, ys[-1], THICK)
    for (t, _), ya, yb in zip(heights, ys, ys[1:]):
        sh.text((x1 + x2) / 2, (ya + yb) / 2, t, 2.5, "center", 90)
    # графы 24, 25: «Перв. примен.», «Справ. №» — 2 х 60 мм от верхней рамки
    yt = 5
    for k, t in enumerate(("Перв. примен.", "Справ. N")):
        ya, yb = yt + 60 * k, yt + 60 * (k + 1)
        sh.rect(x1, ya, x3, yb, THICK)
        sh.line(x2, ya, x2, yb, THICK)
        sh.text((x1 + x2) / 2, (ya + yb) / 2, t, 2.5, "center", 90)
    if code:
        sh.text((x2 + x3) / 2, yt + 30, code, 3.0, "center", 90)
    # графа 26: обозначение, повёрнутое на 180°, 70 х 14 в левом верхнем углу
    # (только чертежи и схемы)
    if not graph26:
        return
    sh.rect(20, 5, 90, 19, THICK)
    if code:
        sh.text(55, 12, code, 4.5, "center", 180)


# ---------------------------------------------------------------- вывод

def _q(s):
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"')


def to_wks(sh, path, page1only=True):
    """Оформление листа KiCad. Координаты — от левого верхнего угла листа."""
    opt = " (option page1only)" if page1only else ""
    out = ['(kicad_wks (version 20231118) (generator "pl_editor") (generator_version "9.0")',
           '  (setup (textsize 2.5 2.5) (linewidth %.2f) (textlinewidth 0.25)' % THIN,
           '    (left_margin 0) (right_margin 0) (top_margin 0) (bottom_margin 0))']
    for x1, y1, x2, y2, wd in sh.lines:
        out.append('  (line (name "") (start %.3f %.3f ltcorner) (end %.3f %.3f ltcorner)%s (linewidth %.2f))'
                   % (x1, y1, x2, y2, opt, wd))
    for x, y, s, size, just, ang in sh.texts:
        j = {"left": " (justify left)", "center": " (justify center)", "right": " (justify right)"}[just]
        rot = " (rotate %d)" % ang if ang else ""
        out.append('  (tbtext %s (name "") (pos %.3f %.3f ltcorner)%s (font%s (size %.2f %.2f))%s%s)'
                   % (_q(s), x, y, opt, ' (face "%s")' % FONT if FONT else "", size, size, j, rot))
    out.append(")")
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")

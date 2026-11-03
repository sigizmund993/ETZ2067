"""Плата из netlist.py + layout.py, трассировка Freerouting, заливка земли.

    python3 gen_pcb.py place    -> ../etz_plata.kicad_pcb (только расстановка)
    python3 gen_pcb.py route    -> + Freerouting, полигоны, DRC

Посадочные места привязаны к символам схемы (path = /uuid символа), поэтому
в KiCad работает «Обновить плату по схеме» и проверка соответствия.
"""
import json, os, subprocess, sys
import pcbnew
import netlist as N
import layout as LY
from gen_sch import U, PROJECT, OUT

FP_DIR = os.environ.get("KICAD_FP_DIR", "/usr/share/kicad/footprints")
PCB = os.path.join(OUT, PROJECT + ".kicad_pcb")
PRO = os.path.join(OUT, PROJECT + ".kicad_pro")
FREEROUTING = os.path.expanduser("~/tools/freerouting/freerouting-2.5.0-linux-x64/bin/freerouting")
OX, OY = 50.0, 50.0          # левый верхний угол платы на листе

MM = pcbnew.FromMM


def V(x, y):
    return pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))


# классы цепей: ширина дорожки, зазор
CLASSES = {
    "Default": dict(track=0.3, clear=0.2, via=0.7, drill=0.35),
    "Power": dict(track=1.2, clear=0.3, via=1.0, drill=0.5),
    "Motor": dict(track=0.7, clear=0.25, via=0.9, drill=0.45),
    "Ground": dict(track=0.6, clear=0.25, via=0.8, drill=0.4),
}


def net_class(net):
    if net.startswith("M1_") or net.startswith("M2_"):
        return "Motor"
    if net == "GND":
        return "Ground"
    if net in N.POWER_NETS:
        return "Power"
    return "Default"


def write_project():
    pro = {}
    if os.path.exists(PRO):
        pro = json.load(open(PRO, encoding="utf-8"))
    classes = []
    for name, c in CLASSES.items():
        classes.append({"name": name, "track_width": c["track"], "clearance": c["clear"],
                        "via_diameter": c["via"], "via_drill": c["drill"],
                        "microvia_diameter": 0.3, "microvia_drill": 0.1,
                        "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25,
                        "wire_width": 6, "bus_width": 12, "line_style": 0,
                        "schematic_color": "rgba(0, 0, 0, 0.000)", "pcb_color": "rgba(0, 0, 0, 0.000)",
                        "priority": 2147483647 if name == "Default" else 0})
    nets = sorted({n for p in N.PARTS for n in p["pins"].values()})
    # цепи с локальными метками на корневом листе называются "/ИМЯ"
    patterns = [{"netclass": net_class(n), "pattern": "/" + n} for n in nets if net_class(n) != "Default"]
    pro.setdefault("meta", {"filename": PROJECT + ".kicad_pro", "version": 3})
    pro["net_settings"] = {"classes": classes, "meta": {"version": 4},
                           "net_colors": None, "netclass_assignments": None,
                           "netclass_patterns": patterns}
    erc = pro.setdefault("erc", {}).setdefault("rule_severities", {})
    erc["power_pin_not_driven"] = "ignore"     # питание приходит снаружи платы (АКБ, USB)
    sch = pro.setdefault("schematic", {})
    sch.setdefault("drawing", {})["default_text_size"] = 98.4     # 2.5 мм в милах
    sch["page_layout_descr_file"] = "gost_A3.kicad_wks"
    pro.setdefault("pcbnew", {}).setdefault("page_layout_descr_file", "")
    json.dump(pro, open(PRO, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def load_fp(fpid):
    lib, name = fpid.split(":")
    fp = pcbnew.FootprintLoad(os.path.join(FP_DIR, lib + ".pretty"), name)
    if fp is None:
        raise RuntimeError("нет посадочного места " + fpid)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def outline(board, w, h, r=3.0):
    def seg(a, b):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(*a)); s.SetEnd(V(*b))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1))
        board.Add(s)

    def arc(c, a0):
        import math
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetCenter(V(*c))
        s.SetStart(V(c[0] + r * math.cos(math.radians(a0)), c[1] + r * math.sin(math.radians(a0))))
        s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1))
        board.Add(s)
    seg((r, 0), (w - r, 0)); seg((w, r), (w, h - r)); seg((w - r, h), (r, h)); seg((0, h - r), (0, r))
    arc((w - r, r), 270); arc((w - r, h - r), 0); arc((r, h - r), 90); arc((r, r), 180)


def place():
    write_project()
    board = pcbnew.NewBoard(PCB)
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    ds.m_TrackMinWidth = MM(0.15)
    ds.m_CopperEdgeClearance = MM(0.3)     # JLCPCB: от 0,3 мм
    nets = {}

    def net(name):
        name = "/" + name
        if name not in nets:
            ni = pcbnew.NETINFO_ITEM(board, name)
            board.Add(ni)
            nets[name] = ni
        return nets[name]

    import symlib
    for p in N.PARTS:
        ref = p["ref"]
        fp = load_fp(p["fp"])
        fp.SetReference(ref)
        fp.SetValue(p["value"])
        x, y, rot, side = LY.PCB[ref]
        fp.SetPosition(V(x, y))
        fp.SetOrientationDegrees(rot)
        if p["sym"].startswith("Mechanical:"):
            fp.SetBoardOnly(True)
        else:
            fp.SetPath(pcbnew.KIID_PATH("/" + U("sym", ref)))
            fp.SetSheetname("/")
            fp.SetSheetfile(PROJECT + ".kicad_sch")
            # выводы по имени (модуль драйвера) -> номера символа
            conn = {}
            sym = symlib.load(p["sym"])
            spins = symlib.pins(sym)
            for k, n in p["pins"].items():
                if isinstance(k, str) and not k.isdigit():
                    for num, lst in spins.items():
                        if any(t[3] == k for t in lst):
                            conn[num] = n
                else:
                    conn[str(k)] = n
            for pad in fp.Pads():
                n = conn.get(pad.GetNumber())
                if n:
                    pad.SetNet(net(n))
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(MM(0.9), MM(0.9)))
        fp.Reference().SetTextThickness(MM(0.14))
        fp.Value().SetVisible(False)
        board.Add(fp)
        # обозначение — над корпусом (по габариту), горизонтально
        bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if not fp.GetCourtyard(pcbnew.F_CrtYd).IsEmpty() else fp.GetBoundingBox()
        r = fp.Reference()
        r.SetTextAngleDegrees(0)
        r.SetKeepUpright(True)
        cx = (bb.GetLeft() + bb.GetRight()) // 2
        top = bb.GetTop() - MM(0.7)
        if pcbnew.ToMM(top) - OY < 1.0:              # у верхнего края — под корпус
            top = bb.GetBottom() + MM(0.7)
        r.SetPosition(pcbnew.VECTOR2I(cx, top))
    # у разъёмов с подписью и у крепёжных отверстий обозначение — только на
    # сборочном слое (F.Fab), иначе налезает на подпись
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in LABELS or ref.startswith("H") and not ref.startswith("HL"):
            fp.Reference().SetLayer(pcbnew.F_Fab)
    # ON/OFF стабилизаторов (вывод 5) — на теплоотвод (вывод 3, GND) напрямую:
    # между узкими выводами полигон к нему не подходит
    for ref in ("DA1", "DA2"):
        fp = board.FindFootprintByReference(ref)
        p5 = next(pd for pd in fp.Pads() if pd.GetNumber() == "5")
        p3 = max((pd for pd in fp.Pads() if pd.GetNumber() == "3"), key=lambda pd: pd.GetSize().x * pd.GetSize().y)
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(p5.GetPosition())
        t.SetEnd(pcbnew.VECTOR2I(p3.GetPosition().x, p5.GetPosition().y))
        t.SetWidth(MM(0.8)); t.SetLayer(pcbnew.F_Cu); t.SetNet(p5.GetNet())
        t.SetLocked(True)
        board.Add(t)
    outline(board, LY.BOARD_W, LY.BOARD_H)
    # подписи разъёмов на шелкографии
    for ref, txt in LABELS.items():
        x, y, rot, _ = LY.PCB[ref]
        t = pcbnew.PCB_TEXT(board)
        t.SetText(txt)
        dx, dy = LABEL_OFFS.get(ref, (-1.5, 4.8 if y < 10 else -4.6))
        t.SetPosition(V(x + dx, y + dy))
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(MM(1.2), MM(1.2)))
        t.SetTextThickness(MM(0.18))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
        board.Add(t)
    t = pcbnew.PCB_TEXT(board)
    t.SetText("ЕТЗ плата приводов v1\nKiCad 10, 2026")
    t.SetPosition(V(32, 46)); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(MM(1.5), MM(1.5))); t.SetTextThickness(MM(0.22))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    board.Add(t)
    board.Save(PCB)
    return board


LABELS = {
    "X2": "АКБ 3S +", "X3": "ВЫКЛ", "X4": "СТОП", "X5": "ЗЕЛ 12В",
    "X6": "МОТОР 1", "X7": "МОТОР 2", "X8": "MS1 MS2", "X9": "MS1 MS2",
    "X10": "S Z", "X11": "S ROT", "X12": "S CAM", "X13": "ПОМПА", "X14": "КЛАПАН",
    "X15": "КРАСН", "X16": "СТАРТ", "X17": "ХОЛЛ1", "X18": "ХОЛЛ2", "X19": "ВАКУУМ",
    "X20": "А", "X21": "Б", "X22": "В", "X23": "РЕЗЕРВ", "X1": "КОНТРОЛЛЕР",
}
LABEL_OFFS = {"X1": (0, -8.5), "X2": (-13, 11), "X3": (5.5, -5), "X4": (-5.5, 5.3), "X5": (-2.5, 5.2),
              "X6": (11.5, 0), "X7": (11.5, 0), "X13": (-3, 4.3), "X14": (-3, 4.3),
              "X20": (-1.5, -3.2), "X21": (-1.5, -3.2), "X22": (-1.5, -3.2), "X23": (-1.5, -3.2),
              "X10": (-1.5, 3.2), "X11": (-1.5, 3.2), "X12": (-1.5, 3.2)}


def zones(board, fill=True):
    gnd = board.FindNet("/GND")
    for z in list(board.Zones()):
        board.Remove(z)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnd)
        o = z.Outline()
        o.NewOutline()
        for (x, y) in ((0.5, 0.5), (LY.BOARD_W - 0.5, 0.5), (LY.BOARD_W - 0.5, LY.BOARD_H - 0.5),
                       (0.5, LY.BOARD_H - 0.5)):
            o.Append(MM(OX + x), MM(OY + y))
        z.SetMinThickness(MM(0.25))
        z.SetLocalClearance(MM(0.3))
        z.SetThermalReliefGap(MM(0.3))
        z.SetThermalReliefSpokeWidth(MM(0.5))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        board.Add(z)
    if fill:
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())


def stitch(board, step=5.0, r=0.5, margin=0.35):
    """Сшивка полигонов земли переходными отверстиями по сетке — там, где
    круг via с запасом целиком лежит в заливке обоих слоёв."""
    import math
    gnd = board.FindNet("/GND")
    polys = {}
    for z in board.Zones():
        polys[z.GetLayer()] = z.GetFilledPolysList(z.GetLayer())
    n = 0
    y = step / 2
    while y < LY.BOARD_H:
        x = step / 2
        while x < LY.BOARD_W:
            pts = [V(x + (r + margin) * math.cos(a), y + (r + margin) * math.sin(a))
                   for a in [k * math.pi / 4 for k in range(8)]] + [V(x, y)]
            if all(all(pl.Contains(pcbnew.VECTOR2I(p.x, p.y)) for p in pts) for pl in polys.values()):
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(V(x, y))
                v.SetWidth(MM(2 * r)); v.SetDrill(MM(0.4))
                v.SetNet(gnd)
                board.Add(v)
                n += 1
            x += step
        y += step
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    return n


def route():
    board = pcbnew.LoadBoard(PCB)
    # землю роутер тоже ведёт дорожками (0,6 мм): тогда связность не зависит
    # от того, как разрежется заливка; полигоны и сшивка — поверх
    for z in list(board.Zones()):
        board.Remove(z)
    dsn = os.path.join(OUT, "gen", "out", PROJECT + ".dsn")
    ses = dsn[:-4] + ".ses"
    os.makedirs(os.path.dirname(dsn), exist_ok=True)
    if not pcbnew.ExportSpecctraDSN(board, dsn):
        raise RuntimeError("DSN не записан")
    if os.path.exists(ses):
        os.remove(ses)
    cmd = [FREEROUTING, "-de", dsn, "-do", ses, "-mp", "30", "--gui.enabled=false"]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)
    if not pcbnew.ImportSpecctraSES(board, ses):
        raise RuntimeError("SES не прочитан")
    zones(board)
    print("сшивка: %d via" % stitch(board))
    board.Save(PCB)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "place"
    if what == "place":
        place()
    elif what == "route":
        route()
    elif what == "zones":
        b = pcbnew.LoadBoard(PCB)
        zones(b)
        b.Save(PCB)
    print("ok", what)

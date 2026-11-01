"""Разбор G-code Orca (G0/G1 + дуги G2/G3, абсолютные XY) в отрезки экструзии."""
import math, re
NUM = re.compile(r'([XYIJE])([-\d.]+)')


def segments(path, arc_step=0.2):
    z = 0.0; typ = None; x = y = None; out = []
    for line in open(path):
        if line.startswith(';Z:'):
            z = float(line[3:]); continue
        if line.startswith(';TYPE:'):
            typ = line[6:].strip(); continue
        c = line.split(';', 1)[0].strip()
        if not c or c[0] != 'G':
            continue
        g = c.split()[0]
        if g not in ('G0', 'G1', 'G2', 'G3'):
            continue
        p = dict((k, float(v)) for k, v in NUM.findall(c))
        nx, ny = p.get('X', x), p.get('Y', y)
        ext = 'E' in p and p['E'] > 0 and typ not in (None, 'Custom')
        if g in ('G2', 'G3') and x is not None:
            cx, cy = x + p.get('I', 0.0), y + p.get('J', 0.0)
            r = math.hypot(x - cx, y - cy)
            a0 = math.atan2(y - cy, x - cx); a1 = math.atan2(ny - cy, nx - cx)
            if g == 'G2':          # по часовой
                while a1 >= a0: a1 -= 2 * math.pi
            else:
                while a1 <= a0: a1 += 2 * math.pi
            n = max(2, int(abs(a1 - a0) * r / arc_step))
            pts = [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
            if ext:
                out += [(z, typ, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]) for i in range(n)]
        elif ext and x is not None:
            out.append((z, typ, x, y, nx, ny))
        x, y = nx, ny
    return out


def pts_seg(s, step=0.2):
    L = math.hypot(s[4] - s[2], s[5] - s[3]); k = max(1, int(L / step))
    return [(s[2] + (s[4] - s[2]) * i / k, s[3] + (s[5] - s[3]) * i / k) for i in range(k + 1)]

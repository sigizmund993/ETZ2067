"""Добавить в 3MF OrcaSlicer объём-enforcer поддержек к объекту детали.

    make_3mf.py SRC.3mf DST.3mf ENFORCER.stl PART.stl

SRC — 3MF, экспортированный CLI Orca из PART.stl. Enforcer задан в тех же
координатах, что и PART.stl; Orca хранит сетку объекта со своим сдвигом
(центрирует её), сдвиг вычисляется сравнением габаритов STL и сетки в 3MF.
"""
import os, re, struct, sys, zipfile

SRC, DST, ENF, PART = sys.argv[1:5]


def stl_tris(p):
    d = open(p, "rb").read()
    n = struct.unpack("<I", d[80:84])[0]
    return [[struct.unpack("<3f", d[84 + i * 50 + 12 + 12 * k:84 + i * 50 + 24 + 12 * k]) for k in range(3)]
            for i in range(n)]


def bbmin(pts):
    return [min(p[i] for p in pts) for i in range(3)]


part_name = os.path.basename(PART)
zin = zipfile.ZipFile(SRC)
obj_file = next(n for n in zin.namelist() if n.startswith("3D/Objects/" + part_name))
t = zin.read(obj_file).decode("utf-8")
mesh_v = [tuple(map(float, m)) for m in re.findall(r'<vertex x="([-\d.e]+)" y="([-\d.e]+)" z="([-\d.e]+)"', t)]
stl_v = [v for tri in stl_tris(PART) for v in tri]
off = [a - b for a, b in zip(bbmin(stl_v), bbmin(mesh_v))]          # STL = сетка 3MF + off

verts, idx, faces = [], {}, []
for tri in stl_tris(ENF):
    f = []
    for v in tri:
        k = tuple(round(v[i] - off[i], 4) for i in range(3))
        if k not in idx:
            idx[k] = len(verts)
            verts.append(k)
        f.append(idx[k])
    faces.append(f)
obj_id = re.search(r'<object id="(\d+)"', t).group(1)
new_id = "90"
mesh = ['  <object id="%s" p:UUID="00900000-81cb-4c03-9d28-80fed5dfa1dc" type="model">' % new_id,
        "   <mesh>", "    <vertices>"]
mesh += ['     <vertex x="%g" y="%g" z="%g"/>' % v for v in verts]
mesh += ["    </vertices>", "    <triangles>"]
mesh += ['     <triangle v1="%d" v2="%d" v3="%d"/>' % tuple(f) for f in faces]
mesh += ["    </triangles>", "   </mesh>", "  </object>"]
mesh = "\n".join(mesh) + "\n"

_model = zin.read("3D/3dmodel.model").decode("utf-8")
_comp = re.search(r'(<component p:path="/%s" objectid="%s"[^>]*transform="([^"]+)"/>)'
                  % (re.escape(obj_file), obj_id), _model)
main_id = re.search(r'<object id="(\d+)"[^>]*>\s*<components>\s*' + re.escape(_comp.group(1)), _model).group(1)

zout = zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    data = zin.read(it.filename)
    n = it.filename
    if n.startswith("Metadata/plate_") and (n.endswith(".gcode") or n.endswith(".md5")):
        continue                                    # старый G-code — пересоберётся
    if n == obj_file:
        data = data.decode("utf-8").replace(" </resources>", mesh + " </resources>", 1).encode("utf-8")
    elif n == "3D/3dmodel.model":
        s = data.decode("utf-8")
        comp = re.search(r'(<component p:path="/%s" objectid="%s"[^>]*transform="([^"]+)"/>)'
                         % (re.escape(obj_file), obj_id), s)
        new = ('<component p:path="/%s" objectid="%s" p:UUID="00900000-b206-40ff-9872-83e8017abed1" '
               'transform="%s"/>' % (obj_file, new_id, comp.group(2)))
        data = s.replace(comp.group(1), comp.group(1) + "\n    " + new, 1).encode("utf-8")
    elif n == "Metadata/model_settings.config":
        s = data.decode("utf-8")
        m = re.search(r'(<object id="%s">.*?)(\n  </object>)' % main_id, s, re.S)
        mat = re.search(r'key="matrix" value="([^"]+)"', m.group(1)).group(1)
        part = ('\n    <part id="%s" subtype="support_enforcer">\n'
                '      <metadata key="name" value="podderzhki_tolko_tut"/>\n'
                '      <metadata key="matrix" value="%s"/>\n    </part>' % (new_id, mat))
        data = s.replace(m.group(0), m.group(1) + part + m.group(2), 1).encode("utf-8")
    zout.writestr(it, data)
zout.close()
print("ok: enforcer %d треуг., сдвиг сетки %s" % (len(faces), [round(v, 3) for v in off]))

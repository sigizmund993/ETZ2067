"""Развернуть системный профиль OrcaSlicer (цепочку inherits) в полный JSON для CLI."""
import json, os, sys, glob
ROOT = os.path.expanduser("~/Applications/OrcaSlicer/resources/profiles")
_index = {}
for p in glob.glob(os.path.join(ROOT, "**", "*.json"), recursive=True):
    try:
        j = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    if isinstance(j, dict) and "name" in j:
        _index.setdefault(j["name"], []).append(p)

def load(name, vendor="Creality"):
    ps = _index[name]
    ps = sorted(ps, key=lambda p: 0 if "/%s/" % vendor in p else 1)
    return json.load(open(ps[0], encoding="utf-8"))

def flat(name):
    j = load(name)
    base = flat(j["inherits"]) if j.get("inherits") else {}
    base.update({k: v for k, v in j.items() if k != "inherits"})
    return base

def write(name, out, **over):
    j = flat(name)
    j.update(over)
    j["name"] = name
    j["from"] = "system"
    json.dump(j, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return j

if __name__ == "__main__":
    d = os.path.dirname(os.path.abspath(__file__))
    m = write("Creality K2 Plus 0.4 nozzle", os.path.join(d, "machine.json"))
    p = write("0.20mm Strength @Creality K2 Plus 0.4 nozzle", os.path.join(d, "process.json"),
              enable_support="1", support_type="tree(auto)", support_on_build_plate_only="1")
    f = write("Creality Generic PLA @K2-all", os.path.join(d, "filament.json"))
    for k in ("printable_area", "printable_height", "nozzle_diameter"):
        print(k, m.get(k))
    for k in ("layer_height", "wall_loops", "sparse_infill_density", "sparse_infill_pattern",
              "enable_support", "support_type", "support_threshold_angle", "support_on_build_plate_only"):
        print(k, p.get(k))
    for k in ("nozzle_temperature", "hot_plate_temp", "filament_type", "filament_diameter"):
        print(k, f.get(k))

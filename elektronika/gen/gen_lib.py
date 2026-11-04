"""Свой символ: ESP32-S3-DevKitC-1 (Espressif, v1.1) -> ../lib/etz.kicad_sym.

Номера выводов: 1..22 — гребёнка J1, 23..44 — J3 (J3-1 = 23). Модуль на плату
не паяется — стоит в гнёздах XS5 (J1) и XS6 (J3), поэтому посадочного места
у символа нет.
"""
import os
import sexp
from sexp import Sym as S

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "etz.kicad_sym")

J1 = ["3V3", "3V3", "RST", "GPIO4", "GPIO5", "GPIO6", "GPIO7", "GPIO15", "GPIO16", "GPIO17", "GPIO18",
      "GPIO8", "GPIO3", "GPIO46", "GPIO9", "GPIO10", "GPIO11", "GPIO12", "GPIO13", "GPIO14", "5V", "GND"]
J3 = ["GND", "TX/GPIO43", "RX/GPIO44", "GPIO1", "GPIO2", "GPIO42", "GPIO41", "GPIO40", "GPIO39", "GPIO38",
      "GPIO37", "GPIO36", "GPIO35", "GPIO0", "GPIO45", "GPIO48", "GPIO47", "GPIO21", "GPIO20", "GPIO19",
      "GND", "GND"]


def eff(size=1.27, hide=False):
    e = [S("effects"), [S("font"), [S("size"), size, size]]]
    if hide:
        e.append([S("hide"), S("yes")])
    return e


def pin(num, name, x, y, ang):
    t = "power_in" if name in ("3V3", "5V", "GND") else ("input" if name == "RST" else "bidirectional")
    return [S("pin"), S(t), S("line"), [S("at"), x, y, ang], [S("length"), 3.81],
            [S("name"), name, eff()], [S("number"), str(num), eff()]]


def main():
    W, n = 15.24, 22
    top = (n - 1) * 2.54 / 2
    body = [S("symbol"), "ESP32-S3-DevKitC-1_0_1",
            [S("rectangle"), [S("start"), -W + 3.81, top + 2.54], [S("end"), W - 3.81, -top - 2.54],
             [S("stroke"), [S("width"), 0.254], [S("type"), S("default")]], [S("fill"), [S("type"), S("background")]]]]
    pins = [S("symbol"), "ESP32-S3-DevKitC-1_1_1"]
    for i, nm in enumerate(J1):
        pins.append(pin(i + 1, nm, -W, top - 2.54 * i, 0))
    for i, nm in enumerate(J3):
        pins.append(pin(23 + i, nm, W, top - 2.54 * i, 180))
    sym = [S("symbol"), "ESP32-S3-DevKitC-1", [S("pin_names"), [S("offset"), 1.016]],
           [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
           [S("property"), "Reference", "A", [S("at"), 0, top + 5.08, 0], eff(1.27)],
           [S("property"), "Value", "ESP32-S3-DevKitC-1", [S("at"), 0, -top - 5.08, 0], eff(1.27)],
           [S("property"), "Footprint", "", [S("at"), 0, 0, 0], eff(1.27, True)],
           [S("property"), "Datasheet",
            "https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html",
            [S("at"), 0, 0, 0], eff(1.27, True)],
           [S("property"), "Description", "Плата ESP32-S3-DevKitC-1 (J1: 1-22, J3: 23-44)", [S("at"), 0, 0, 0],
            eff(1.27, True)],
           body, pins]
    lib = [S("kicad_symbol_lib"), [S("version"), 20241209], [S("generator"), "etz_gen"],
           [S("generator_version"), "1.0"], sym]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(sexp.dump(lib) + "\n")


if __name__ == "__main__":
    main()

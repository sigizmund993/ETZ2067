"""Состав и соединения платы приводов ETZ — единственный источник правды.

Из него строятся и схема (Э3), и плата, и перечень элементов (ПЭ3), так что
они не расходятся. Позиционные обозначения — по ГОСТ 2.710 (A, C, DA, FU,
HL, L, R, VD, VT, X).

Контроллер — ESP32-S3-DevKitC-1 (A3), съёмный: стоит в гнёздах XS5 (J1) и
XS6 (J3) на самой плате. Логика 3.3 В (+3V3 — с вывода 3V3 модуля), +5V на
датчики и разъём «В» — с вывода 5V модуля (USB ноутбука, ЕТЗ п. 3.3).
Дисплей 0,96" ST7735S 80x160 — прямо на выводы ESP32 (логика 3.3 В).

Драйверы — сменные модули StepStick в гнёздах XS1-XS4 (по две гребёнки
PBS-8 на модуль); модули A1, A2, A3 на плату не паяются (on_board=False).

Цепи:
  VBAT      аккумулятор 3S после разъёма
  VBAT_F    после предохранителя
  VSW       после выключателя (дальше — кнопка останова)
  VMOT      силовая шина приводов: после кнопки останова (горит HL1)
  +5V_SRV   серво (DA1), +6V_PMP — помпа и клапан (DA2)
  +5V, +3V3 от модуля ESP32 (USB)
"""

# (обозначение, символ, номинал, посадочное место, {вывод: цепь}, примечание для ПЭ3)
# вывод — номер вывода символа/посадочного места
PARTS = []


def part(ref, sym, value, fp, pins, name=None, note="", on_board=True):
    PARTS.append(dict(ref=ref, sym=sym, value=value, fp=fp, pins=pins, name=name, note=note,
                      on_board=on_board))


R0805 = "Resistor_SMD:R_0805_2012Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"

# ---------------------------------------------------------------- питание
part("X2", "Connector_Generic:Conn_01x02", "XT60-M", "Connector_AMASS:AMASS_XT60-M_1x02_P7.20mm_Vertical",
     {1: "VBAT", 2: "GND"}, "Вилка XT60-M вертикальная", "АКБ 3S")
part("FU1", "Device:Fuse", "5 А", "Fuse:Fuseholder_Blade_Mini_Keystone_3568",
     {1: "VBAT", 2: "VBAT_F"}, "Держатель предохранителя Keystone 3568 с предохранителем Mini 5 А")
part("VD1", "Device:D_Zener", "SMBJ15A", "Diode_SMD:D_SMB",
     {1: "VBAT_F", 2: "GND"}, "Диод защитный SMBJ15A")
part("X3", "Connector_Generic:Conn_01x02", "DG301-5.0-02", "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
     {1: "VBAT_F", 2: "VSW"}, "Клеммник винтовой 2 конт. 5,08 мм", "Выключатель")
part("X4", "Connector_Generic:Conn_01x02", "DG301-5.0-02", "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
     {1: "VSW", 2: "VMOT"}, "Клеммник винтовой 2 конт. 5,08 мм", "Кнопка останова")
part("C1", "Device:C_Polarized", "470 мкФ 25 В", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm",
     {1: "VMOT", 2: "GND"}, "Конденсатор алюминиевый 470 мкФ 25 В")
part("R1", "Device:R", "2,2 кОм", R0805, {1: "VMOT", 2: "N_HL1"}, "Резистор 0805 2,2 кОм ±5%")
part("HL1", "Device:LED", "зелёный", "LED_THT:LED_D5.0mm",
     {1: "GND", 2: "N_HL1"}, "Светодиод 5 мм зелёный", "Приводы под напряжением")
part("R2", "Device:R", "10 кОм", R0805, {1: "VMOT", 2: "ESTOP_S"}, "Резистор 0805 10 кОм ±1%")
part("R3", "Device:R", "2,7 кОм", R0805, {1: "ESTOP_S", 2: "GND"}, "Резистор 0805 2,7 кОм ±1%")
part("C2", "Device:C", "0,1 мкФ", C0805, {1: "ESTOP_S", 2: "GND"}, "Конденсатор 0805 X7R 0,1 мкФ")

# DA1: 5 В на серво (фиксированный), DA2: 6 В на помпу (регулируемый)
part("DA1", "Regulator_Switching:LM2596S-5", "LM2596S-5.0", "Package_TO_SOT_SMD:TO-263-5_TabPin3",
     {1: "VMOT", 2: "SW1", 3: "GND", 4: "+5V_SRV", 5: "GND"}, "Микросхема LM2596S-5.0")
part("C3", "Device:C_Polarized", "220 мкФ 25 В", "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
     {1: "VMOT", 2: "GND"}, "Конденсатор алюминиевый 220 мкФ 25 В")
part("VD2", "Device:D_Schottky", "SS54", "Diode_SMD:D_SMC", {1: "SW1", 2: "GND"}, "Диод Шоттки SS54")
part("L1", "Device:L", "33 мкГн", "Inductor_SMD:L_Bourns_SRR1260", {1: "SW1", 2: "+5V_SRV"},
     "Дроссель SRR1260-330M 33 мкГн 4 А")
part("C4", "Device:C_Polarized", "470 мкФ 10 В", "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
     {1: "+5V_SRV", 2: "GND"}, "Конденсатор алюминиевый 470 мкФ 10 В")

part("DA2", "Regulator_Switching:LM2596S-ADJ", "LM2596S-ADJ", "Package_TO_SOT_SMD:TO-263-5_TabPin3",
     {1: "VMOT", 2: "SW2", 3: "GND", 4: "FB2", 5: "GND"}, "Микросхема LM2596S-ADJ")
part("C5", "Device:C_Polarized", "220 мкФ 25 В", "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
     {1: "VMOT", 2: "GND"}, "Конденсатор алюминиевый 220 мкФ 25 В")
part("VD3", "Device:D_Schottky", "SS54", "Diode_SMD:D_SMC", {1: "SW2", 2: "GND"}, "Диод Шоттки SS54")
part("L2", "Device:L", "33 мкГн", "Inductor_SMD:L_Bourns_SRR1260", {1: "SW2", 2: "+6V_PMP"},
     "Дроссель SRR1260-330M 33 мкГн 4 А")
part("C6", "Device:C_Polarized", "220 мкФ 16 В", "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
     {1: "+6V_PMP", 2: "GND"}, "Конденсатор алюминиевый 220 мкФ 16 В")
part("R4", "Device:R", "3,9 кОм", R0805, {1: "+6V_PMP", 2: "FB2"}, "Резистор 0805 3,9 кОм ±1%",
     "")
part("R5", "Device:R", "1 кОм", R0805, {1: "FB2", 2: "GND"}, "Резистор 0805 1 кОм ±1%")

# ---------------------------------------------------------------- шаговые
for i, (a, x, cc, st, dr, ua, ms) in enumerate((("A1", "X6", "C7", "STEP1", "DIR1", "UART1", "X8"),
                                                 ("A2", "X7", "C8", "STEP2", "DIR2", "UART2", "X9"))):
    n = i + 1
    # выводы модуля Pololu/StepStick; под TMC2209: MS3 -> PDN_UART, ~RESET -> PDN_UART
    # (на модуле они соединены), ~SLEEP -> CLK (на GND — внутренний генератор)
    part(a, "Driver_Motor:Pololu_Breakout_A4988", "TMC2209", "",
         {"~{ENABLE}": "EN", "MS1": "MS1_%d" % n, "MS2": "MS2_%d" % n, "MS3": ua,
          "~{RESET}": ua, "~{SLEEP}": "GND", "STEP": st, "DIR": dr,
          "VMOT": "VMOT", "GND": "GND", "VDD": "+3V3",
          "1A": "M%d_1A" % n, "1B": "M%d_1B" % n, "2A": "M%d_2A" % n, "2B": "M%d_2B" % n},
         "Модуль драйвера шагового двигателя TMC2209 (StepStick)",
         ("Плечо" if n == 1 else "Предплечье") + ", в XS%d, XS%d" % (2 * n - 1, 2 * n), on_board=False)
    # гнёзда модуля: левая гребёнка — выводы 1..8 модуля (мотор, питание),
    # правая — 16..9 (логика), шаг между рядами 12.7
    part("XS%d" % (2 * n - 1), "Connector_Generic:Conn_01x08", "PBS-8",
         "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical",
         {1: "GND", 2: "+3V3", 3: "M%d_1B" % n, 4: "M%d_1A" % n, 5: "M%d_2A" % n, 6: "M%d_2B" % n,
          7: "GND", 8: "VMOT"}, "Розетка PBS-8 1x8 2,54 мм", "Под A%d" % n)
    part("XS%d" % (2 * n), "Connector_Generic:Conn_01x08", "PBS-8",
         "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical",
         {1: dr, 2: st, 3: "GND", 4: ua, 5: ua, 6: "MS2_%d" % n, 7: "MS1_%d" % n, 8: "EN"},
         "Розетка PBS-8 1x8 2,54 мм", "Под A%d" % n)
    part(x, "Connector_Generic:Conn_01x04", "XH-4A", "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical",
         {1: "M%d_2B" % n, 2: "M%d_2A" % n, 3: "M%d_1A" % n, 4: "M%d_1B" % n},
         "Вилка JST XH 4 конт.", "Мотор плеча" if n == 1 else "Мотор предплечья")
    part(cc, "Device:C_Polarized", "100 мкФ 25 В", "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
         {1: "VMOT", 2: "GND"}, "Конденсатор алюминиевый 100 мкФ 25 В")
    part(ms, "Connector_Generic:Conn_02x02_Odd_Even", "PLD-4", "Connector_PinHeader_2.54mm:PinHeader_2x02_P2.54mm_Vertical",
         {1: "MS1_%d" % n, 2: "+3V3", 3: "MS2_%d" % n, 4: "+3V3"},
         "Вилка штыревая 2x2 2,54 мм", "Шаг 1/8 без перемычек")

part("R6", "Device:R", "10 кОм", R0805, {1: "+3V3", 2: "EN"}, "Резистор 0805 10 кОм ±5%",
     "")

# ---------------------------------------------------------------- серво
for j, (x, sig, r, name) in enumerate((("X10", "SRV1", "R7", "Серво Z"),
                                       ("X11", "SRV2", "R8", "Серво поворота"),
                                       ("X12", "SRV3", "R9", "Серво камеры"))):
    part(x, "Connector_Generic:Conn_01x03", "PLS-3", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
         {1: "%s_O" % sig, 2: "+5V_SRV", 3: "GND"}, "Вилка штыревая 1x3 2,54 мм", name + "")
    part(r, "Device:R", "220 Ом", R0805, {1: sig, 2: "%s_O" % sig}, "Резистор 0805 220 Ом ±5%")

# ---------------------------------------------------------------- ключи
for k, (vt, sig, rg, rp, vd, x, load, net) in enumerate((
        ("VT1", "PUMP", "R10", "R11", "VD4", "X13", "Помпа 6 В", "PMP_D"),
        ("VT2", "VALVE", "R12", "R13", "VD5", "X14", "Клапан 6 В (НО)", "VLV_D"))):
    part(vt, "Transistor_FET:AO3400A", "AO3400A", "Package_TO_SOT_SMD:SOT-23",
         {1: sig + "_G", 2: "GND", 3: net}, "Транзистор AO3400A")
    part(rg, "Device:R", "100 Ом", R0805, {1: sig, 2: sig + "_G"}, "Резистор 0805 100 Ом ±5%")
    part(rp, "Device:R", "100 кОм", R0805, {1: sig + "_G", 2: "GND"}, "Резистор 0805 100 кОм ±5%")
    part(vd, "Device:D_Schottky", "SS34", "Diode_SMD:D_SMA", {1: "+6V_PMP", 2: net}, "Диод Шоттки SS34")
    part(x, "Connector_Generic:Conn_01x02", "XH-2A", "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
         {1: "+6V_PMP", 2: net}, "Вилка JST XH 2 конт.", load)

# красный индикатор выполнения программы
part("VT3", "Transistor_FET:AO3400A", "AO3400A", "Package_TO_SOT_SMD:SOT-23",
     {1: "LED_R_G", 2: "GND", 3: "LED_R_K"}, "Транзистор AO3400A")
part("R14", "Device:R", "100 Ом", R0805, {1: "LED_R", 2: "LED_R_G"}, "Резистор 0805 100 Ом ±5%")
part("R15", "Device:R", "100 кОм", R0805, {1: "LED_R_G", 2: "GND"}, "Резистор 0805 100 кОм ±5%")
part("R16", "Device:R", "330 Ом", R0805, {1: "+5V", 2: "LED_R_A"}, "Резистор 0805 330 Ом ±5%")
part("HL2", "Device:LED", "красный", "LED_THT:LED_D5.0mm",
     {1: "LED_R_K", 2: "LED_R_A"}, "Светодиод 5 мм красный", "Выполнение программы")

# ---------------------------------------------------------------- кнопки
# SB1 — «Старт» (ЕТЗ п. 3.5), SB2/SB3 — выбор задачи и параметров
for b, (sb, sig, r, c, note) in enumerate((("SB1", "START", "R17", "C9", "«Старт»"),
                                          ("SB2", "BTN2", "R24", "C13", "Выбор"),
                                          ("SB3", "BTN3", "R25", "C14", "Ввод"))):
    part(sb, "Switch:SW_Push", "6x6", "Button_Switch_THT:SW_PUSH_6mm_H8.5mm",
         {1: sig, 2: "GND"}, "Кнопка тактовая 6x6 мм, h 8,5", note)
    part(r, "Device:R", "10 кОм", R0805, {1: "+3V3", 2: sig}, "Резистор 0805 10 кОм ±5%")
    part(c, "Device:C", "0,1 мкФ", C0805, {1: sig, 2: "GND"}, "Конденсатор 0805 X7R 0,1 мкФ")

# ---------------------------------------------------------------- дисплей
# модуль 0,96" ST7735S 80x160 SPI в гнезде X24; порядок выводов — как у
# распространённых модулей: GND VCC SCL SDA RES DC CS BLK (сверить с купленным!)
part("X24", "Connector_Generic:Conn_01x08", "PBS-8", "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical",
     {1: "GND", 2: "+3V3", 3: "DISP_SCK", 4: "DISP_MOSI", 5: "DISP_RST", 6: "DISP_DC", 7: "DISP_CS",
      8: "DISP_BL"}, "Розетка PBS-8 1x8 2,54 мм", "Дисплей 0,96\" ST7735S")

# ---------------------------------------------------------------- датчики
for h, (x, sig, r) in enumerate((("X17", "HALL1", "R18"), ("X18", "HALL2", "R19"))):
    part(x, "Connector_Generic:Conn_01x03", "XH-3A", "Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical",
         {1: "+5V", 2: "GND", 3: sig}, "Вилка JST XH 3 конт.",
         "Холл плеча" if h == 0 else "Холл предплечья")
    part(r, "Device:R", "10 кОм", R0805, {1: "+3V3", 2: sig}, "Резистор 0805 10 кОм ±5%")
part("X19", "Connector_Generic:Conn_01x03", "PBS-3", "Connector_PinSocket_2.54mm:PinSocket_1x03_P2.54mm_Vertical",
     {1: "+5V", 2: "GND", 3: "VAC_IN"}, "Розетка PBS-3 1x3 2,54 мм", "Модуль датчика вакуума XGZP6847A")
part("R20", "Device:R", "10 кОм", R0805, {1: "VAC_IN", 2: "VAC"}, "Резистор 0805 10 кОм ±1%",
     "")
part("R21", "Device:R", "20 кОм", R0805, {1: "VAC", 2: "GND"}, "Резистор 0805 20 кОм ±1%")
part("C10", "Device:C", "0,1 мкФ", C0805, {1: "VAC", 2: "GND"}, "Конденсатор 0805 X7R 0,1 мкФ")

# ---------------------------------------------------------------- разъёмы ЕТЗ (п. 3.6)
part("X20", "Connector_Generic:Conn_01x03", "PLS-3", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
     {1: "A_SIG", 2: "+3V3", 3: "GND"}, "Вилка штыревая 1x3 2,54 мм", "Разъём «А»")
part("X21", "Connector_Generic:Conn_01x03", "PLS-3", "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
     {1: "B_HV", 2: "+3V3", 3: "GND"}, "Вилка штыревая 1x3 2,54 мм", "Разъём «Б»")
part("VT4", "Transistor_FET:BSS138", "BSS138", "Package_TO_SOT_SMD:SOT-23",
     {1: "+3V3", 2: "B_SIG", 3: "B_HV"}, "Транзистор BSS138", "")
part("R22", "Device:R", "10 кОм", R0805, {1: "+3V3", 2: "B_SIG"}, "Резистор 0805 10 кОм ±5%")
part("R23", "Device:R", "10 кОм", R0805, {1: "+5V", 2: "B_HV"}, "Резистор 0805 10 кОм ±5%")
part("X22", "Connector_Generic:Conn_01x04", "PLS-4", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
     {1: "C_TX", 2: "C_RX", 3: "+5V", 4: "GND"}, "Вилка штыревая 1x4 2,54 мм", "Разъём «В»")
part("C11", "Device:C", "10 мкФ", C1206, {1: "+5V", 2: "GND"}, "Конденсатор 1206 X5R 10 мкФ 16 В")
part("C12", "Device:C", "0,1 мкФ", C0805, {1: "+3V3", 2: "GND"}, "Конденсатор 0805 X7R 0,1 мкФ")

# ---------------------------------------------------------------- контроллер
# ESP32-S3-DevKitC-1: какой GPIO куда. Не заняты: 0 (BOOT), 19/20 (USB),
# 43/44 (UART0 — USB-UART модуля, связь с ноутбуком), 35-37 (PSRAM у N8R8 и
# N16R8). 45 и 46 — выводы начальной загрузки: на них затворы ключей помпы и
# клапана с подтяжкой 100 кОм к земле, то есть при сбросе они как раз низкие.
J1 = {1: "+3V3", 2: "+3V3", 4: "A_SIG", 5: "HALL1", 6: "HALL2", 7: "START", 8: "BTN2", 9: "BTN3",
      10: "C_TX", 11: "C_RX", 12: "B_SIG", 13: "LED_R", 14: "VALVE", 15: "DISP_DC", 16: "DISP_CS",
      17: "DISP_MOSI", 18: "DISP_SCK", 19: "DISP_BL", 20: "DISP_RST", 21: "+5V", 22: "GND"}
J3 = {1: "GND", 4: "VAC", 5: "ESTOP_S", 6: "EN", 7: "DIR2", 8: "STEP2", 9: "DIR1", 10: "STEP1",
      15: "PUMP", 16: "SRV3", 17: "SRV2", 18: "SRV1", 21: "GND", 22: "GND"}
part("A3", "etz:ESP32-S3-DevKitC-1", "ESP32-S3-DevKitC-1", "",
     dict(list(J1.items()) + [(22 + k, v) for k, v in J3.items()]),
     "Модуль ESP32-S3-DevKitC-1 (N8R2 или N16R8)", "В XS5, XS6", on_board=False)
part("XS5", "Connector_Generic:Conn_01x22", "PBS-22", "Connector_PinSocket_2.54mm:PinSocket_1x22_P2.54mm_Vertical",
     J1, "Розетка PBS-22 1x22 2,54 мм", "Под A3, гребёнка J1")
part("XS6", "Connector_Generic:Conn_01x22", "PBS-22", "Connector_PinSocket_2.54mm:PinSocket_1x22_P2.54mm_Vertical",
     J3, "Розетка PBS-22 1x22 2,54 мм", "Под A3, гребёнка J3")

for m in range(1, 5):
    part("H%d" % m, "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3",
         {}, None)

POWER_NETS = {"VBAT", "VBAT_F", "VSW", "VMOT", "GND", "SW1", "SW2", "+5V_SRV", "+6V_PMP",
              "PMP_D", "VLV_D"} | {"M%d_%s" % (n, c) for n in (1, 2) for c in ("1A", "1B", "2A", "2B")}

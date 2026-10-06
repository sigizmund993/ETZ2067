# ETZ — полигон ВсОШ Робототехника 2026-27 (проектный тур)

Проект: 3D-модель полигона по краткому ЕТЗ (техзадание) для проектного тура
ВсОШ по робототехнике, сезон 2026-27. Модель строится в FreeCAD.

## Файлы проекта

- [etz_kratko_26_27_копия.pdf](etz_kratko_26_27_копия.pdf) — исходное ТЗ (23 стр.), источник всех размеров/требований.
- [ETZ_poligon.FCMacro](ETZ_poligon.FCMacro) — **основной скрипт-генератор модели** (Python). Пересобирает документ `ETZ_Poligon` с нуля при каждом запуске (`App.closeDocument` + `App.newDocument`). Правки вносятся сюда, а не руками в .FCStd.
- [ETZ_Poligon.FCStd](ETZ_Poligon.FCStd) — сохранённый документ FreeCAD (результат работы макроса), открыт прямо сейчас в GUI.
- `freecad-mcp.mcpb` — упакованное расширение для Claude Desktop (см. ниже). Выдано пользователю, в репозитории не обязательно хранить дальше.
- `freecad-mcpb/manifest.json` — исходник манифеста, из которого собран `.mcpb` (на случай пересборки, напр. при добавлении auth-токена).

## Версионирование модели — History Workbench

В FreeCAD поставлен аддон [History Workbench](https://github.com/eblanshey/HistoryWorkbench)
(0.2.1, LGPL-2.1) — git-версионирование `.FCStd` через GUI (diff в 3D и по дереву
документа, без необходимости знать git). Установлен вручную (клон репозитория
скопирован в Mod, как и для MCP-аддона — Addon Manager делает то же самое):
`~/.var/app/org.freecad.FreeCAD/data/FreeCAD/v1-1/Mod/HistoryWorkbench/`
(копировались только `package.xml`, `README.md`, `LICENSE`, `freecad/history_wb/`;
`.git`, `tests/`, `docs-static-site/`, dev-скрипты — не нужны в рантайме).

Зависимости проверены и в порядке: системный `git` (2.49.0) и `PyYAML` (6.0.3,
уже был в питоне самого FreeCAD) доступны изнутри flatpak-песочницы FreeCAD —
несмотря на sandbox, `filesystems=host` в правах flatpak даёт доступ и к
хостовым бинарникам. Подтверждено после рестарта: `Gui.listWorkbenches()`
содержит `HistoryWorkbench` без ошибок импорта.

Пользоваться: переключить workbench на "History" в выпадающем списке в GUI
FreeCAD, "Initialize Project" → выбрать папку `/home/semen/ETZ`. Проверил по
исходнику аддона (`git_port_adapter.py`, `initialize_repository()`): он просто
вызывает `git init` в указанной папке — если там уже есть `.git` (а он уже
есть, см. ниже), git-init по нему идёт безопасно повторно и репозиторий
переиспользуется, **это тот же самый `/home/semen/ETZ/.git`**, отдельного
репозитория аддон не заводит. Коммитит через `git add -- <конкретные файлы>`
(не `-A`), то есть сам по себе не утащит в коммит что попало — стейджит только
то, что выбрано в его UI (обычно `.FCStd`).

## Что строит макет (ETZ_poligon.FCMacro)

Глобальная СК: начало — левый нижний угол полигона 600×500 мм, X вправо, Y вверх,
Z вверх от поверхности. Координаты поля ЕТЗ (п. 2.2) переводятся через
`field_to_global()`, начало поля O = центр метки ArUco id 27.

Группы объектов в документе:
- **Полигон** (5 объектов) — основание, зона 1 (350×500), зона 2 (верх/низ, 250×80 каждая), область операционного поля (250×330).
- **Операционное поле** (13 объектов) — лист А4-шаблон, чёрные ограничительные полосы, красная сетка 9×6 клеток по 28 мм, чёрные круги Ø6 и зелёные окружности Ø24,5 в центрах клеток + столбец отбоя, три метки ArUco (DICT_4X4_50, id 27/28/29) с чёрными/белыми частями, оси поля.
- **Шашки** (по 2 объекта на штуку: корпус + шайба) — расставляются по списку `CHECKERS` в начале макроса: `(клетка, цвет[, высота_стопки])`. Клетка — `"Б3"` (буква А..Е = ряд, цифра = столбец) или `"Отбой1".."Отбой5"`. Шашка: Ø26×5, крышка 0,8 мм, стенка 0,9 мм; внутри шайба М8 (ГОСТ 6958-78) Ø24×2 с отверстием Ø8,4, прилегает к крышке.

Чтобы переставить/перекрасить шашки или изменить расстановку — правь только список
`CHECKERS` и/или словарь `COLORS` в начале файла, затем пересобери документ (см. ниже).

## Как пересобрать модель

Через MCP (`execute_code` на документе, либо headless):
```python
exec(compile(open('/home/semen/ETZ/ETZ_poligon.FCMacro', encoding='utf-8').read(),
             '/home/semen/ETZ/ETZ_poligon.FCMacro', 'exec'), {'__name__': '__main__'})
```
Макрос сам закрывает старый документ `ETZ_Poligon` и строит заново, затем делает
`viewIsometric()` + `ViewFit`. После пересборки стоит сохранить:
```python
App.getDocument('ETZ_Poligon').save()
```

## MCP-подключение к FreeCAD (как это работает)

Установлен официальный **freecad-mcp** (neka-nat, https://github.com/neka-nat/freecad-mcp), версия **0.1.25**. Два независимых компонента:

1. **Аддон внутри FreeCAD** (workbench "MCP Addon") — поднимает XML-RPC сервер
   на `127.0.0.1:9875`. Установлен в
   `~/.var/app/org.freecad.FreeCAD/data/FreeCAD/v1-1/Mod/FreeCADMCP/`
   (FreeCAD запущен как **flatpak**, `org.freecad.FreeCAD`, 1.1.3 — это важно,
   пути Mod/настроек у flatpak свои, см. ниже).
   Автостарт сервера включён через файл настроек аддона:
   `~/.var/app/org.freecad.FreeCAD/data/FreeCAD/v1-1/freecad_mcp_settings.json`
   (`"auto_start_rpc": true`) — сервер поднимается сам при каждом запуске
   FreeCAD, кнопку жать не нужно.
2. **MCP-сервер** `freecad-mcp` (pip-пакет, `pip install --user freecad-mcp`,
   бинарник `/home/semen/.local/bin/freecad-mcp`) — это именно то, с чем
   говорит Claude по протоколу MCP (stdio). Внутри он сам ходит по XML-RPC к
   порту 9875. Нужен Python ≥3.12 (системный `python3` на машине — 3.12.3,
   подходит; Python самого FreeCAD — 3.13, это другое, отдельное окружение).

Эти два компонента общаются только друг с другом через localhost:9875 — FreeCAD
должен быть запущен (с аддоном) **до** того, как Claude дёргает инструменты.

### Как подключено к Claude

Собран и установлен `.mcpb`-бандл (`freecad-mcp.mcpb`, через официальный CLI
`@anthropic-ai/mcpb`, `npx @anthropic-ai/mcpb pack`). В `manifest.json` —
`"server": {"type": "binary", "mcp_config": {"command": "/home/semen/.local/bin/freecad-mcp", "args": ["--only-text-feedback"]}}`.
Код сервера НЕ забандлен внутрь `.mcpb` — манифест просто указывает на уже
установленный путь, это рабочий вариант (`type: "binary"` не обязан быть
внутри архива).

Поставлено пользователем через **Settings → Extensions → install file** в
Claude Desktop (это НЕ обычный open-source Claude Desktop — внутреннее
приложение c "cowork"/"epitaxy"-движком; отдельного CLI `claude` тут нет,
`claude mcp add` не работает, классический `claude_desktop_config.json` с
ключом `mcpServers` тоже не читается — MCP-серверы живут только как
расширения `.dxt/.mcpb` через Settings → Extensions либо как коннекторы из
реестра через Settings → Connectors).

Подключение проверено end-to-end (см. чейнджлог) — Claude Desktop сам
спавнит процесс `freecad-mcp --only-text-feedback` (родитель —
`/usr/lib/claude-desktop/claude-desktop`), тот коннектится к FreeCAD, видит
документ `ETZ_Poligon`.

**Важный нюанс:** список MCP-инструментов сессии Claude фиксируется при
старте. Если FreeCAD только что переоткрыт/переустановлен аддон — новые
инструменты появятся только в **новом чате**, не в текущем.

## Чейнджлог

- **2026-10-06.** Прочитано ТЗ (PDF) и исходный `ETZ_poligon.FCMacro`.
  Обнаружено, что FreeCAD не установлен в PATH/apt/snap, но уже стоит как
  **flatpak** `org.freecad.FreeCAD` 1.1.3 (`flatpak info org.freecad.FreeCAD`).
  Запущен на реальном X11-дисплее пользователя (`DISPLAY=:1`, активная сессия
  `seat0`), flatpak-права включают `filesystems=host` — доступ к обычным путям
  вроде `/home/semen/...` есть, а вот `/tmp` у flatpak-приложений **изолирован**
  (писать временные файлы для обмена с FreeCAD нужно только под `/home/semen/...`,
  не под `/tmp`).
  - Собран и опробован **самодельный RPC-мост** (сокет-сервер на QTimer внутри
    FreeCAD + питоновский клиент) — временное решение, чтобы управлять FreeCAD
    программно без скриншотов. Через него найдена и исправлена реальная
    ошибка в макросе: `GridLines` красился в `(0.88, 0, 0)` — смесь
    float/int в одном RGB-кортеже, из-за чего `ViewObject.ShapeColor = color`
    падал с `TypeError: Type in tuple must be consistent (float)` на
    современном FreeCAD 1.1 / Python 3.13. Исправлено на `(0.88, 0.0, 0.0)`.
    После фикса модель собирается полностью (35 объектов).
  - По просьбе пользователя самодельный мост **полностью удалён** (сам процесс
    FreeCAD с ним убит, файлы `rpc_bridge.FCMacro`/`rpc_client.py`/пробные
    файлы стёрты без следов) и заменён на официальный **freecad-mcp**.
  - Поставлен аддон (`addon/FreeCADMCP` из репозитория neka-nat/freecad-mcp) в
    Mod-папку flatpak-инсталляции, включён автостарт RPC через
    `freecad_mcp_settings.json`, установлен pip-пакет `freecad-mcp` в
    `~/.local/bin`.
  - Первая попытка подключить это к Claude (дописать `mcpServers` в
    `~/.config/Claude/claude_desktop_config.json`) была **отменена после
    проверки** — выяснилось, что этот файл в данной сборке Claude не имеет
    отношения к MCP (внутреннее состояние интерфейса), а MCP-серверы здесь
    управляются как расширения `.dxt/.mcpb` (см. `extensions-blocklist.json`,
    ключи `dxt:allowlist*`) через Settings → Extensions.
  - Собран `.mcpb`-бандл через `@anthropic-ai/mcpb` (`npx`, т.к. глобальный
    `npm install -g` требовал root), провалидирован, передан пользователю.
    Пользователь поставил его через Settings → Extensions.
  - Подключение проверено: смоделирован полный MCP-хендшейк тем же бинарником
    (список из 17 инструментов, `get_rpc_status` → `version_check: "ok"`,
    `list_documents` → `["ETZ_Poligon"]`), и отдельно подтверждено по `ps`,
    что Claude Desktop сам держит процесс `freecad-mcp` (родитель —
    `claude-desktop`), то есть расширение реально используется приложением,
    не только моей симуляцией.
  - Текущее состояние модели сохранено в `ETZ_Poligon.FCStd`.
  - Инициализирован **git** в `/home/semen/ETZ` (`git init`, `.gitignore` для
    `*.FCStd1/.FCBak/__pycache__`), сделан первый коммит `a9173a9` со всеми
    файлами проекта.
  - По вопросу "есть ли удобный аддон для git в FreeCAD" — найден и поставлен
    **[History Workbench](https://github.com/eblanshey/HistoryWorkbench)**
    (0.2.1): склонирован, в Mod скопированы только
    `package.xml`/`README.md`/`LICENSE`/`freecad/history_wb/` (без `.git`,
    `tests/`, `docs-static-site/` — не нужны в рантайме). Зависимости
    (системный `git`, `PyYAML`) проверены через `execute_code` — обе доступны
    изнутри flatpak-песочницы. FreeCAD пересохранён и перезапущен (`kill -9` +
    повторный `flatpak run`), после рестарта `Gui.listWorkbenches()`
    подтвердил `HistoryWorkbench` в списке без ошибок импорта.

## Известные нюансы / грабли на будущее

- Flatpak FreeCAD: **не используй `/tmp`** для файлов, которыми обмениваешься
  с процессом FreeCAD — пиши в `/home/semen/ETZ` или другой путь под `$HOME`.
- `pkill -f FreeCAD` в этом окружении почему-то не проходит через
  sandbox-разрешения Bash-тула (тихо фейлится, даёт `Exit code 1` без вывода).
  Используй `kill -9 <pid>` по явным PID из `ps aux`.
- Цвета `ViewObject.ShapeColor` в современном FreeCAD требуют **однородного**
  типа внутри кортежа — либо все int, либо все float, смешивать нельзя.
- Если меняешь `CHECKERS`/геометрию и видишь похожую ошибку — ищи такие же
  смешанные кортежи по аналогии.
- `freecad-mcp` требует Python ≥3.12 на стороне MCP-сервера — это системный
  `python3`, НЕ питон самого FreeCAD (у FreeCAD 1.1 свой встроенный 3.13,
  отдельный от системного).
- Если переустанавливаешь аддон или обновляешь `freecad-mcp` — версии должны
  совпадать (`get_rpc_status` → `version_check`), иначе будет варнинг о
  рассинхроне; после обновления аддона — перезапусти FreeCAD.

# Дизайн: веб-версия визуализатора сортировок

- **Дата:** 2026-07-02
- **Отношение к А-01:** второй фронт над тем же ядром. Desktop-версия (PySide6) остаётся без изменений.
- **Стек:** Python 3.12+, FastAPI, uvicorn; фронтенд — ванильный JS + Canvas (без фреймворка/сборщика).
- **Мотивация:** для десктоп-GUI Docker неудобен (нужен X-сервер). Веб-версия делает контейнеризацию буквальной: `docker run -p 8000:8000` → `localhost:8000`, без настройки окружения.

## 1. Цель и объём

Веб-приложение с полным паритетом функций desktop-версии:
- одиночный режим: выбор алгоритма, play/пауза, шаг вперёд/назад, скорость, размер, способ заполнения, счётчики операций;
- режим гонки: 4 алгоритма на одном массиве;
- серверное хранение массивов (JSON) и экспорт статистики (CSV).

**Переиспользование (без изменений):** весь `sorting_visualizer/core/` (события, 4 алгоритма, `fill`, `stats`, `runner`, `Timeline`) и `sorting_visualizer/io/` (array_store, stats_export). Оба слоя Qt-free — подтверждено. Существующие 72 теста не трогаем.

**Не трогаем:** `sorting_visualizer/ui/` и `sorting_visualizer/app.py` (desktop).

### Зафиксированные решения (брейнсторминг)
| Вопрос | Решение |
|---|---|
| Хранение файлов | Серверное: JSON-массивы в `data/arrays/`, CSV в `data/exports/` (обёртки над `io/`) |
| Что запускает Docker | Веб-сервер (uvicorn); desktop остаётся локальным |
| Объём функций | Полный паритет с desktop |
| Модель проигрывания | Сервер отдаёт лог событий JSON, браузер проигрывает (JS-Timeline) |
| Стек | FastAPI + ванильный JS + Canvas |

## 2. Архитектура

Ещё один фронт над ядром, как `ui/`. Направление зависимостей: **web → core/io**. Ядро не знает про веб.

```
sorting_visualizer/web/
  __init__.py
  server.py            # FastAPI: роуты + отдача статики + main()
  serialization.py     # Event/Recording <-> dict
  storage.py           # серверное хранение: data/ dir, list/save/load массивов, export CSV
  static/
    index.html
    app.js
    styles.css
tests/web/
  __init__.py
  test_serialization.py
  test_api_record.py
  test_api_storage.py
  test_api_export.py
requirements-web.txt     # fastapi, uvicorn[standard], httpx, pytest (без PySide6)
Dockerfile               # ИЗМЕНЯЕМ → веб-образ (uvicorn)
README.md                # ДОПОЛНЯЕМ разделом про веб
```

### Поток данных
1. Браузер: `POST /api/generate {size, fill}` → массив.
2. Одиночный: `POST /api/record {algorithm, data}` → `{initial, events, stats, elapsed_ms}`. Браузер строит JS-Timeline и проигрывает.
3. Гонка: `POST /api/race {data}` → рекординги всех 4 алгоритмов на одном массиве; 4 canvas двигаются общим интервалом.
4. Смена алгоритма в одиночном режиме — повторный `/api/record` по тому же `data` (без регенерации).

## 3. Бэкенд (FastAPI) — `server.py`

Pydantic-модели запросов/ответов. Роуты:

| Метод | Путь | Тело | Ответ |
|---|---|---|---|
| GET | `/` | — | `static/index.html` |
| POST | `/api/generate` | `{size:int, fill:str, seed?:int}` | `{data:[int]}` |
| POST | `/api/record` | `{algorithm:str, data:[int]}` | `Recording` |
| POST | `/api/race` | `{data:[int]}` | `{recordings:{name:Recording}}` |
| GET | `/api/arrays` | — | `{names:[str]}` |
| PUT | `/api/arrays/{name}` | `{data:[int], fill:str}` | `{ok:true}` |
| GET | `/api/arrays/{name}` | — | `{data:[int], fill:str}` |
| POST | `/api/export-stats` | `{rows:[StatsRow]}` | CSV-файл (attachment) |

- Статика монтируется (`StaticFiles`); `GET /` отдаёт `index.html`.
- `fill` валидируется как `FillMode`; `size` в диапазоне 10–200 (иначе 422).
- `/api/record` использует `runner.record(ALGORITHMS[algorithm], data)`; неизвестный алгоритм → 404.

### Обработка ошибок
| Ситуация | Ответ |
|---|---|
| `ArrayLoadError` (битый/несуществующий сохранённый массив) | 400/404 + сообщение |
| Неизвестный алгоритм | 404 |
| Некорректные параметры (size вне диапазона, неизвестный fill) | 422 (pydantic/валидатор) |
| Ошибка записи файла (`OSError`) | 500 + сообщение |

Фронтенд ловит не-2xx и показывает сообщение пользователю.

## 4. Сериализация — `serialization.py`

Чистые функции, без FastAPI (тестируются изолированно).

- `event_to_dict(Event) -> dict`: `Compare→{"type":"compare","i","j"}`, `Swap→{"type":"swap","i","j"}`, `Overwrite→{"type":"overwrite","i","value","old"}`, `MarkSorted→{"type":"marksorted","i"}`.
- `event_from_dict(dict) -> Event`: обратное преобразование.
- `recording_to_dict(Recording) -> dict`: `{initial, events:[...], stats:{comparisons,writes}, elapsed_ms}`.

## 5. Серверное хранение — `storage.py`

Тонкая обёртка над `io/`, задающая управляемую директорию данных (по умолчанию `./data`, переопределяется env `SV_DATA_DIR`).

- `arrays_dir()` / `exports_dir()` — создают подпапки при необходимости.
- `list_arrays() -> list[str]` — имена `.json` в `data/arrays/`.
- `save_array(name, data, fill)` — `io.array_store.save(arrays_dir()/f"{name}.json", data, fill)`.
- `load_array(name) -> LoadedArray` — `io.array_store.load(...)`; пробрасывает `ArrayLoadError`.
- `export_stats(rows) -> Path` — пишет CSV в `data/exports/{timestamp}.csv` через `io.stats_export.export`, возвращает путь.
- Имя массива санитизируется (только `[A-Za-z0-9_-]`), чтобы исключить обход путей.

## 6. Фронтенд — `static/`

- `index.html`: две вкладки (Single / Race), панель контролов, `<canvas>`(ы), строка статистики, кнопки Save/Load/Export.
- `app.js`:
  - **JS-Timeline** — зеркало питоновского: локальное состояние `{data, sorted:Set, highlight:[], kind:""}`; `applyEvent`/`revertEvent` (для `swap` — обмен, `overwrite` — запись `value`/откат `old`, `marksorted` — добавить/убрать индекс, `compare` — подсветка); `stepForward/stepBack/reset`.
  - **Рендер Canvas** — столбики (высота ∝ значению), цвет по роли: normal `#B0B0B0`, compare `#F2C037`, move `#E5484D`, sorted `#46A758`.
  - **Проигрывание** — `setInterval` по значению ползунка скорости; стоп в конце, кнопка play возвращается в исходное.
  - **Гонка** — 4 canvas, один интервал двигает все таймлайны; финишировавший замирает.
  - **Fetch** — вызовы API; Save/Load/Export; ошибки не-2xx → сообщение.
- `styles.css` — раскладка (grid для 4 панелей гонки).

## 7. Тестирование

- `tests/web/` (pytest + FastAPI `TestClient`, зависимость `httpx`):
  - `test_serialization.py`: round-trip `event_to_dict`/`event_from_dict` для всех типов; `recording_to_dict` структура.
  - `test_api_record.py`: `/api/generate` даёт массив нужного размера; `/api/record` для каждого алгоритма — **контракт: события из ответа, десериализованные и проигранные, дают отсортированный массив**; `/api/race` возвращает 4 рекординга; неизвестный алгоритм → 404; size вне диапазона → 422.
  - `test_api_storage.py`: `PUT` затем `GET /api/arrays/{name}` round-trip; `GET` несуществующего → 404/400; `GET /api/arrays` перечисляет сохранённое; санитизация имени.
  - `test_api_export.py`: `/api/export-stats` возвращает CSV с корректным заголовком и строками; файл создаётся в `data/exports/`.
  - Тесты используют временную `SV_DATA_DIR` (tmp_path), чтобы не писать в рабочую папку.
- Существующие 72 теста (core/io/ui) — без изменений.
- Фронтенд: отдельный JS-тулчейн не вводим (YAGNI). Гарантия корректности данных, доходящих до браузера, обеспечивается контрактным тестом `/api/record` (события реально сортируют). JS-Timeline — тонкое зеркало проверенной питоновской логики.

## 8. Docker (изменяем → веб)

- `requirements-web.txt`: `fastapi`, `uvicorn[standard]`, `httpx`, `pytest>=8`. Без PySide6 — образ Qt-free и лёгкий, X-сервер не нужен.
- Dockerfile:
  - `FROM python:3.12-slim`; `pip install -r requirements-web.txt`.
  - `COPY . .`
  - `RUN python -m pytest tests/core tests/io tests/web` — прогон релевантных тестов в билде (без `tests/ui`, т.к. PySide6 в образе нет).
  - `EXPOSE 8000`; `CMD ["uvicorn", "sorting_visualizer.web.server:app", "--host", "0.0.0.0", "--port", "8000"]`.
- `.dockerignore` дополняется `data/` (не тащить локальные данные в образ).
- Запуск: `docker build -t sorting-visualizer-web . && docker run -p 8000:8000 sorting-visualizer-web` → `http://localhost:8000`.
- README: раздел «Веб-версия» — локальный запуск (`uvicorn ...`) и Docker.

### Локальный запуск (dev)
Тот же venv: доустановить `pip install -r requirements-web.txt`, затем
`uvicorn sorting_visualizer.web.server:app --reload` → `http://localhost:8000`.

## 9. Что явно вне объёма (YAGNI)
- Аутентификация, многопользовательность, БД.
- Фронтенд-фреймворки и сборщики (React/webpack).
- WebSocket-стриминг (событий немного, JSON-лог целиком — достаточно).
- Изменение desktop-версии.

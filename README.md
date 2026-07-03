# Визуализатор алгоритмов сортировки (A-01)

Студент: Апросимов Д.В., группа БИС-24-3  
Вариант: A-01 – Визуализатор алгоритмов сортировки

Десктопное и веб-приложение для пошаговой визуализации четырех алгоритмов сортировки:

- Пузырьковая сортировка
- Сортировка вставками
- Сортировка слиянием
- Быстрая сортировка

## Основные возможности

- Пошаговая анимация – сравнения и перестановки элементов подсвечиваются цветом.
- Режим «гонки» – одновременный запуск всех четырех алгоритмов на одинаковых массивах.
- Настройка параметров – изменение размера массива (10–100 элементов), типа заполнения (случайный, обратный, почти отсортированный) и скорости анимации.
- Статистика – отображение количества сравнений, обменов и времени выполнения каждого алгоритма.
- Сохранение данных – массивы сохраняются в формате JSON, статистика экспортируется в CSV.
- Две версии приложения – десктопная (PySide6) и веб-версия (FastAPI + HTML/JavaScript).
- Контейнеризация – Docker-образы для десктопной и веб-версии приложения.

---

## Требования

- Python 3.9 или выше
- Docker (для запуска в контейнерах)
- X-сервер (только для десктопной версии Docker на Windows/macOS)

---

## Установка и локальный запуск

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/Kennenestephong/sorting-visualizer.git
cd sorting-visualizer
```

### 2. Создайте виртуальное окружение

#### Windows (cmd)

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Установите зависимости

#### Для десктопной версии

```bash
pip install -r requirements.txt
```

#### Для веб-версии

```bash
pip install -r requirements-web.txt
```

### 4. Запуск приложения

#### Десктопная версия

```bash
python -m sorting_visualizer.app
```

#### Веб-версия

```bash
uvicorn sorting_visualizer.web.server:app --reload
```

После запуска откройте браузер по адресу:

```
http://localhost:8000
```

---

## Запуск тестов

Запуск всех тестов:

```bash
python -m pytest tests -v
```

Запуск тестов без графического интерфейса:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest tests
```

---

## Контейнеризация (Docker)

### Веб-версия

#### Сборка образа

```bash
docker build -t sorting-visualizer-web .
```

#### Запуск контейнера

```bash
docker run -p 8000:8000 sorting-visualizer-web
```

После запуска откройте:

```
http://localhost:8000
```

---

### Десктопная версия

#### Сборка образа

```bash
docker build -f Dockerfile.desktop -t sorting-visualizer-desktop .
```

#### Запуск на Linux

```bash
xhost +local:docker
docker run --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix sorting-visualizer-desktop
```

#### Запуск на Windows/macOS (с использованием X-сервера, например VcXsrv или XQuartz)

```bash
docker run --rm -e DISPLAY=host.docker.internal:0 sorting-visualizer-desktop
```

#### Headless-запуск (без графического интерфейса)

```bash
docker run --rm -e QT_QPA_PLATFORM=offscreen sorting-visualizer-desktop
```

---

## Запуск тестов в Docker

### Веб-версия

```bash
docker run --rm sorting-visualizer-web python -m pytest tests/core tests/io tests/web -v
```

### Десктопная версия

```bash
docker run --rm -e QT_QPA_PLATFORM=offscreen sorting-visualizer-desktop python -m pytest tests -v
```
# Knowledge Diff

Track changes in documentation pages and discover what changed since you last read them.

Отслеживайте изменения в документации и быстро узнавайте, что поменялось с момента последнего чтения.

## English

### What is it?

Knowledge Diff is a Python CLI tool that tracks documentation pages by URL, stores local snapshots in SQLite, and shows a readable diff when the content changes.

### Why use it?

- Documentation changes quietly.
- Important sections can be added, removed, or rewritten.
- You may want a lightweight local history without a browser extension or a hosted service.

### Features

- Track pages with `knowdiff add <url>`
- List tracked pages with `knowdiff list`
- Re-check all pages or one page with `knowdiff check`
- Save snapshots only when content changes
- Export the latest diff report to Markdown
- Use a local SQLite database by default
- Override the database location with `KNOWDIFF_DB`
- Run as `knowdiff` or `python -m knowdiff`

### Installation

```bash
py -m pip install -e .
```

For development:

```bash
py -m pip install -e .[dev]
```

### Quick start

```bash
knowdiff add https://react.dev/reference/react/useEffect
knowdiff list
knowdiff check
knowdiff export https://react.dev/reference/react/useEffect --output report.md
```

### CLI commands

#### `knowdiff add <url>`

Fetch a page, extract readable content, split it into sections, and save the first snapshot.

#### `knowdiff list`

Show all tracked pages with URL, snapshot count, and last check time.

#### `knowdiff check`

Check every tracked page and save a new snapshot only if the page changed.

#### `knowdiff check <url>`

Check one tracked page.

#### `knowdiff remove <url>`

Remove a tracked page together with its snapshots and diff records.

#### `knowdiff export <url> --output report.md`

Export the latest stored diff for one URL to a Markdown report.

### Example output

```text
Checking 2 pages...

CHANGED: React useEffect
https://react.dev/reference/react/useEffect

Added sections:
- Common mistakes

Removed sections:
- Legacy behavior

Changed sections:
- Specifying reactive dependencies
- Troubleshooting

UNCHANGED: FastAPI Background Tasks
https://fastapi.tiangolo.com/tutorial/background-tasks/
```

### Architecture overview

- `cli.py`: Typer commands and CLI error handling
- `service.py`: application use cases
- `db.py`: SQLite persistence
- `fetcher.py`: HTTP fetching and URL validation
- `parser.py`: HTML cleanup and section extraction
- `differ.py`: deterministic section diffing
- `renderer.py`: Rich terminal rendering
- `export.py`: Markdown report export

### Development

Run the local quality checks before opening a pull request:

```bash
py -m pytest --cov=knowdiff --cov-report=term-missing
py -m ruff check .
py -m mypy knowdiff tests
py -m bandit -r knowdiff
py -m radon cc knowdiff tests -s
py -m radon mi knowdiff tests -s
py -m xenon --max-absolute B --max-modules A --max-average A knowdiff tests
```

### Open source files

- `LICENSE`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- GitHub Actions CI in `.github/workflows/ci.yml`

### Roadmap

- snapshot history browsing
- ignore rules for noisy sections
- scheduled checks
- machine-readable JSON export

## Русский

### Что это такое?

Knowledge Diff — это Python CLI-инструмент, который отслеживает страницы документации по URL, хранит локальные снимки в SQLite и показывает понятный diff, когда содержимое меняется.

### Зачем это нужно?

- Документация часто меняется незаметно.
- Важные разделы могут появляться, исчезать или переписываться.
- Иногда нужна лёгкая локальная история без браузерного расширения и без внешнего сервиса.

### Возможности

- Отслеживание страниц через `knowdiff add <url>`
- Просмотр списка через `knowdiff list`
- Повторная проверка всех страниц или одной страницы через `knowdiff check`
- Сохранение snapshot только при реальных изменениях
- Экспорт последнего diff-отчёта в Markdown
- Использование локальной SQLite-базы по умолчанию
- Переопределение пути к базе через `KNOWDIFF_DB`
- Запуск как `knowdiff` или `python -m knowdiff`

### Установка

```bash
py -m pip install -e .
```

Для разработки:

```bash
py -m pip install -e .[dev]
```

### Быстрый старт

```bash
knowdiff add https://react.dev/reference/react/useEffect
knowdiff list
knowdiff check
knowdiff export https://react.dev/reference/react/useEffect --output report.md
```

### CLI-команды

#### `knowdiff add <url>`

Загружает страницу, извлекает читаемый текст, разбивает его на секции и сохраняет первый snapshot.

#### `knowdiff list`

Показывает все отслеживаемые страницы, URL, число snapshot и время последней проверки.

#### `knowdiff check`

Проверяет все отслеживаемые страницы и сохраняет новый snapshot только если страница изменилась.

#### `knowdiff check <url>`

Проверяет одну отслеживаемую страницу.

#### `knowdiff remove <url>`

Удаляет отслеживаемую страницу вместе со snapshot и diff-записями.

#### `knowdiff export <url> --output report.md`

Экспортирует последний сохранённый diff для одного URL в Markdown-отчёт.

### Пример вывода

```text
Checking 2 pages...

CHANGED: React useEffect
https://react.dev/reference/react/useEffect

Added sections:
- Common mistakes

Removed sections:
- Legacy behavior

Changed sections:
- Specifying reactive dependencies
- Troubleshooting

UNCHANGED: FastAPI Background Tasks
https://fastapi.tiangolo.com/tutorial/background-tasks/
```

### Обзор архитектуры

- `cli.py`: команды Typer и обработка ошибок CLI
- `service.py`: прикладные сценарии использования
- `db.py`: SQLite-хранилище
- `fetcher.py`: HTTP-запросы и валидация URL
- `parser.py`: очистка HTML и извлечение секций
- `differ.py`: детерминированное сравнение секций
- `renderer.py`: терминальный вывод через Rich
- `export.py`: экспорт Markdown-отчётов

### Разработка

Перед открытием pull request запустите локальные проверки:

```bash
py -m pytest --cov=knowdiff --cov-report=term-missing
py -m ruff check .
py -m mypy knowdiff tests
py -m bandit -r knowdiff
py -m radon cc knowdiff tests -s
py -m radon mi knowdiff tests -s
py -m xenon --max-absolute B --max-modules A --max-average A knowdiff tests
```

### Open source-файлы

- `LICENSE`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- GitHub Actions CI в `.github/workflows/ci.yml`

### Дорожная карта

- просмотр истории snapshot
- правила игнорирования шумных секций
- проверки по расписанию
- экспорт JSON для интеграций

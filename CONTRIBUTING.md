# Contributing / Участие в проекте

## English

Thanks for your interest in improving Knowledge Diff.

### Development setup

```bash
py -m pip install -e .[dev]
py -m pytest
py -m ruff check .
py -m mypy knowdiff tests
```

### Contribution guidelines

1. Open an issue first for large changes.
2. Keep pull requests focused and small.
3. Add or update tests for behavior changes.
4. Keep user-facing documentation in English and Russian.
5. Run the local checks before opening a pull request.

### Pull request checklist

- The change solves one clearly described problem.
- Tests pass locally.
- Lint and type checks pass locally.
- README or docs were updated if behavior changed.
- New instructions are duplicated in English and Russian.

## Русский

Спасибо за интерес к развитию Knowledge Diff.

### Настройка окружения

```bash
py -m pip install -e .[dev]
py -m pytest
py -m ruff check .
py -m mypy knowdiff tests
```

### Правила внесения изменений

1. Для крупных изменений сначала создайте issue.
2. Делайте pull request узким и сфокусированным.
3. Добавляйте или обновляйте тесты при изменении поведения.
4. Поддерживайте пользовательскую документацию на английском и русском.
5. Перед открытием pull request запускайте локальные проверки.

### Чеклист для pull request

- Изменение решает одну чётко описанную проблему.
- Тесты проходят локально.
- Lint и type-check проходят локально.
- README или документация обновлены, если поведение поменялось.
- Новые инструкции продублированы на английском и русском.


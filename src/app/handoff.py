from __future__ import annotations

from pathlib import Path

from app.storage import Order


def handoff_filename(order_id: int, title: str) -> str:
    return f"order-{order_id}-handoff.md"


def build_codex_handoff(order: Order) -> str:
    revision_block = order.revision_notes.strip() or "Правок пока нет."
    deliverable_block = order.deliverable.strip() or "Результат еще не отправлялся."
    return "\n".join(
        [
            f"# Codex task: order #{order.id} - {order.title}",
            "",
            "## Контекст заказа",
            "",
            f"- Order ID: {order.id}",
            f"- Status: {order.status}",
            f"- Контакт заказчика: {order.contact}",
            f"- Created at: {order.created_at}",
            f"- Updated at: {order.updated_at}",
            "",
            "## ТЗ от заказчика",
            "",
            order.brief.strip(),
            "",
            "## Последние правки",
            "",
            revision_block,
            "",
            "## Последний результат",
            "",
            deliverable_block,
            "",
            "## Задача для Codex",
            "",
            "1. Разобрать ТЗ и текущие правки.",
            "2. Реализовать работу end-to-end в целевом проекте.",
            "3. Если контекста не хватает, явно перечислить вопросы перед рискованными изменениями.",
            "4. Подготовить результат, который можно отдать заказчику на апрув.",
            "",
            "## Definition of Done",
            "",
            "- Требования из ТЗ реализованы.",
            "- Правки из последнего блока учтены.",
            "- Код читаемый, без секретов и лишних зависимостей.",
            "- Добавлены или обновлены релевантные тесты.",
            "- Проверки пройдены.",
            "- Commit and push выполнены после успешной проверки.",
            "",
            "## Проверка",
            "",
            "Минимальная команда для Python-проекта:",
            "",
            "```powershell",
            "python -m pytest -q",
            "```",
            "",
        ]
    )


def write_codex_handoff(order: Order, output_dir: str | Path) -> Path:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / handoff_filename(order.id, order.title)
    target_path.write_text(build_codex_handoff(order), encoding="utf-8")
    return target_path

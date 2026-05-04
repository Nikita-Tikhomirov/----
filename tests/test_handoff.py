from app.handoff import build_codex_handoff, handoff_filename
from app.storage import Order


def test_build_codex_handoff_contains_order_context_and_codex_instructions():
    order = Order(
        id=7,
        lead_id=None,
        contact="@client_dev",
        title="Лендинг",
        brief="Сверстать HTML/CSS/JS лендинг с формой заявки",
        status="revision_requested",
        deliverable="https://example.com",
        revision_notes="Поправить мобильную форму",
        created_at="2026-05-04 10:00:00",
        updated_at="2026-05-04 12:00:00",
    )

    content = build_codex_handoff(order)

    assert "# Codex task: order #7 - Лендинг" in content
    assert "Контакт заказчика: @client_dev" in content
    assert "Сверстать HTML/CSS/JS лендинг" in content
    assert "Поправить мобильную форму" in content
    assert "python -m pytest -q" in content
    assert "Commit and push" in content


def test_handoff_filename_is_stable_and_ascii():
    assert handoff_filename(12, "Лендинг: HTML/CSS!") == "order-12-handoff.md"

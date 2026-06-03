from app.storage import Storage


def test_deduplicates_posts_by_channel_and_message_id(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()

    first = storage.save_post(
        channel="jobs",
        message_id=42,
        post_url="https://t.me/jobs/42",
        text="Нужно сверстать лендинг",
        posted_at="2026-05-04T10:00:00+03:00",
    )
    second = storage.save_post(
        channel="jobs",
        message_id=42,
        post_url="https://t.me/jobs/42",
        text="Нужно сверстать лендинг",
        posted_at="2026-05-04T10:00:00+03:00",
    )

    assert first == second
    assert storage.count_posts() == 1


def test_get_lead_for_post_returns_existing_lead(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="jobs",
        message_id=43,
        post_url="https://t.me/jobs/43",
        text="Нужно сверстать лендинг",
        posted_at="2026-05-04T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=81,
        summary="HTML/CSS лендинг",
        draft_reply="Здравствуйте! Готов помочь.",
        contact="@client_dev",
    )

    lead = storage.get_lead_for_post(post_id)

    assert lead is not None
    assert lead.id == lead_id
    assert lead.status == "new"


def test_lead_reply_and_last_error_can_be_updated(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="jobs",
        message_id=44,
        post_url="https://t.me/jobs/44",
        text="Нужно сверстать лендинг",
        posted_at="2026-05-04T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=80,
        summary="HTML/CSS лендинг",
        draft_reply="Старый отклик",
        contact="@client_dev",
    )

    storage.update_lead_reply(lead_id, "Новый отклик")
    storage.mark_failed(lead_id, "Kwork submit button was not found")

    failed = storage.get_lead(lead_id)
    assert failed.draft_reply == "Новый отклик"
    assert failed.status == "failed"
    assert "submit button" in failed.last_error

    storage.mark_lead_emailed(lead_id, "<lead@example.com>")
    assert storage.get_lead(lead_id).last_error == ""


def test_approval_can_be_recorded_only_once(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="jobs",
        message_id=42,
        post_url="https://t.me/jobs/42",
        text="Нужно сверстать лендинг",
        posted_at="2026-05-04T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=80,
        summary="HTML/CSS лендинг",
        draft_reply="Здравствуйте! Готов помочь.",
        contact="@client_dev",
    )

    assert storage.record_approval(lead_id, "<approval@example.com>") is True
    assert storage.record_approval(lead_id, "<approval@example.com>") is False
    assert storage.get_lead(lead_id).status == "approved"


def test_order_lifecycle_accepts_revisions_and_done_approval(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()

    order_id = storage.create_order(
        contact="@client_dev",
        title="Лендинг",
        brief="Сверстать HTML/CSS/JS лендинг",
    )

    assert storage.get_order(order_id).status == "received"

    storage.start_order(order_id)
    assert storage.get_order(order_id).status == "in_progress"

    storage.submit_order_for_approval(order_id, "Готовая ссылка: https://example.com")
    assert storage.get_order(order_id).status == "ready_for_approval"

    assert storage.request_order_revision(
        order_id,
        "<revision-1@example.com>",
        "Поправить мобильную форму",
    )
    order = storage.get_order(order_id)
    assert order.status == "revision_requested"
    assert order.revision_notes == "Поправить мобильную форму"

    storage.start_order(order_id)
    storage.submit_order_for_approval(order_id, "Исправленная версия: https://example.com")

    assert storage.approve_order(order_id, "<done-1@example.com>")
    assert storage.approve_order(order_id, "<done-1@example.com>") is False
    assert storage.get_order(order_id).status == "done"


def test_order_reviews_are_ignored_outside_approval_state(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    order_id = storage.create_order(
        contact="@client_dev",
        title="Лендинг",
        brief="Сверстать HTML/CSS/JS лендинг",
    )

    assert storage.request_order_revision(order_id, "<fix@example.com>", "Поправить") is False
    assert storage.approve_order(order_id, "<done@example.com>") is False
    assert storage.seen_order_review_message_ids() == set()


def test_order_created_from_lead_keeps_original_order_text(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_text = "Нужно сверстать лендинг HTML/CSS/JS, поправить форму. Контакт @client_dev"
    post_id = storage.save_post(
        channel="jobs",
        message_id=43,
        post_url="https://t.me/jobs/43",
        text=post_text,
        posted_at="2026-05-04T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=85,
        summary="HTML/CSS лендинг",
        draft_reply="Здравствуйте! Готов помочь.",
        contact="@client_dev",
    )

    order_id = storage.create_order_from_lead(lead_id)

    assert storage.get_lead(lead_id).post_text == post_text
    assert storage.get_order(order_id).brief == post_text

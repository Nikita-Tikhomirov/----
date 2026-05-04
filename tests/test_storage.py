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

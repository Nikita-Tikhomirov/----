import sqlite3

from app.storage import LeadAttachment, Storage


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


def test_records_and_reads_durable_post_rejection(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=99,
        post_url="https://kwork.ru/projects/99/view",
        text="Сложный заказ",
        posted_at="2026-05-04T10:00:00+03:00",
    )

    storage.record_post_rejection(post_id, "AI: задача сложнее недельного лимита")

    assert storage.get_post_rejection(post_id) == "AI: задача сложнее недельного лимита"
    rejections = storage.list_post_rejections()
    assert len(rejections) == 1
    assert rejections[0].post_id == post_id
    assert rejections[0].post_url == "https://kwork.ru/projects/99/view"
    assert rejections[0].reason == "AI: задача сложнее недельного лимита"

    storage.clear_post_rejection(post_id)

    assert storage.get_post_rejection(post_id) == ""


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


def test_mobile_hub_delivery_is_claimed_once_and_keeps_lead_actionable(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=49,
        post_url="https://kwork.ru/projects/49/view",
        text="Нужно сверстать страницу",
        posted_at="2026-07-18T12:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=81,
        summary="Верстка",
        draft_reply="Здравствуйте!",
        contact="https://kwork.ru/projects/49/view",
    )

    assert storage.claim_lead_hub_delivery(lead_id) is True
    assert storage.claim_lead_hub_delivery(lead_id) is False
    storage.mark_lead_hub_synced(lead_id, 9001)

    lead = storage.get_lead(lead_id)
    assert lead.status == "new"
    assert lead.hub_lead_id == 9001
    assert storage.claim_lead_hub_delivery(lead_id) is False


def test_only_one_storage_instance_can_claim_new_lead_email_delivery(tmp_path):
    database_path = tmp_path / "leads.sqlite3"
    first_storage = Storage(database_path)
    first_storage.initialize()
    second_storage = Storage(database_path)
    second_storage.initialize()
    post_id = first_storage.save_post(
        channel="jobs",
        message_id=430,
        post_url="https://kwork.ru/projects/430/view",
        text="Нужно сверстать лендинг",
        posted_at="2026-05-04T10:00:00+03:00",
    )
    lead_id = first_storage.create_lead(
        post_id=post_id,
        score=81,
        summary="HTML/CSS лендинг",
        draft_reply="Здравствуйте! Готов помочь.",
        contact="https://kwork.ru/projects/430/view",
    )

    assert first_storage.claim_lead_email_delivery(lead_id) is True
    assert second_storage.claim_lead_email_delivery(lead_id) is False

    first_storage.release_lead_email_delivery(lead_id)

    assert second_storage.claim_lead_email_delivery(lead_id) is True
    second_storage.mark_lead_emailed(lead_id, "<lead-430@example.com>")
    assert first_storage.get_lead(lead_id).status == "emailed"
    assert first_storage.claim_lead_email_delivery(lead_id) is False


def test_begin_lead_send_blocks_repeat_submission_until_status_is_recorded(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="jobs",
        message_id=431,
        post_url="https://kwork.ru/projects/431/view",
        text="Нужно сверстать лендинг",
        posted_at="2026-05-04T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=81,
        summary="HTML/CSS лендинг",
        draft_reply="Здравствуйте! Готов помочь.",
        contact="https://kwork.ru/projects/431/view",
    )

    assert storage.begin_lead_send(lead_id) is True
    assert storage.get_lead(lead_id).status == "sending"
    assert storage.begin_lead_send(lead_id) is False

    storage.mark_sent(lead_id, "https://kwork.ru/projects/431/view", "kwork-project-431")
    assert storage.get_lead(lead_id).status == "sent"


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


def test_lead_assessment_update_preserves_manual_reply_title_and_status(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=145,
        post_url="https://kwork.ru/projects/145/view",
        text="Нужно поправить форму заявки",
        posted_at="2026-05-04T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=65,
        summary="Старая AI-оценка",
        draft_reply="Вручную исправленный отклик",
        contact="https://kwork.ru/projects/145/view",
        proposal_title="Правки формы",
        proposal_price_rub=7000,
        proposal_days=3,
    )
    storage.mark_lead_emailed(lead_id, "<lead-145@example.com>")

    storage.update_lead_assessment(
        lead_id,
        score=88,
        summary="Новая AI-оценка",
        price_rub=12000,
        days=5,
    )

    lead = storage.get_lead(lead_id)
    assert lead.score == 88
    assert lead.summary == "Новая AI-оценка"
    assert lead.proposal_price_rub == 12000
    assert lead.proposal_days == 5
    assert lead.draft_reply == "Вручную исправленный отклик"
    assert lead.proposal_title == "Правки формы"
    assert lead.status == "emailed"


def test_lead_persists_kwork_desired_budget_and_maximum(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=146,
        post_url="https://kwork.ru/projects/146/view",
        text="Нужно сверстать лендинг",
        posted_at="2026-07-21T10:00:00+03:00",
    )

    lead_id = storage.create_lead(
        post_id=post_id,
        score=80,
        summary="Лендинг",
        draft_reply="Здравствуйте!",
        contact="https://kwork.ru/projects/146/view",
        buyer_desired_budget_rub=2000,
        kwork_max_price_rub=6000,
    )

    lead = storage.get_lead(lead_id)
    assert lead.buyer_desired_budget_rub == 2000
    assert lead.kwork_max_price_rub == 6000


def test_mark_failed_keeps_a_diagnostic_message_when_exception_text_is_empty(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=46,
        post_url="https://kwork.ru/projects/46/view",
        text="Нужны правки на сайте",
        posted_at="2026-05-04T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=80,
        summary="Правки",
        draft_reply="Здравствуйте!",
        contact="https://kwork.ru/projects/46/view",
    )

    storage.mark_failed(lead_id)

    assert storage.get_lead(lead_id).last_error == "Причина ошибки не получена."


def test_lead_live_kwork_status_is_persisted_separately_from_the_original_post(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=47,
        post_url="https://kwork.ru/projects/47/view",
        text="Предложений: 2",
        posted_at="2026-05-04T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=80,
        summary="Правки",
        draft_reply="Здравствуйте!",
        contact="https://kwork.ru/projects/47/view",
    )

    storage.update_lead_live_status(lead_id, response_count=6, reason="выше установленного лимита")

    lead = storage.get_lead(lead_id)
    assert lead.live_response_count == 6
    assert lead.live_checked_at
    assert lead.live_reason == "выше установленного лимита"


def test_initialize_backfills_missing_error_for_legacy_failed_lead(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=47,
        post_url="https://kwork.ru/projects/47/view",
        text="Нужны правки на сайте",
        posted_at="2026-05-04T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=80,
        summary="Правки",
        draft_reply="Здравствуйте!",
        contact="https://kwork.ru/projects/47/view",
    )
    with sqlite3.connect(storage.database_path) as conn:
        conn.execute("UPDATE leads SET status = 'failed', last_error = '' WHERE id = ?", (lead_id,))

    storage.initialize()

    assert storage.get_lead(lead_id).last_error == "Причина ошибки не получена."


def test_lead_proposal_fields_are_persisted_independently_from_ai_summary(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=45,
        post_url="https://kwork.ru/projects/45/view",
        text="📌 Старое название заказа\nПредложений: 2",
        posted_at="2026-05-04T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=80,
        summary="Срок: 3 дн.\nЦена: 7000 руб.",
        draft_reply="Старый отклик",
        contact="https://kwork.ru/projects/45/view",
    )

    storage.update_lead_proposal(
        lead_id,
        draft_reply="Новый отклик без цены для заказчика",
        title="Новое название заказа",
        price_rub=12000,
        days=5,
    )

    lead = storage.get_lead(lead_id)
    assert lead.draft_reply == "Новый отклик без цены для заказчика"
    assert lead.proposal_title == "Новое название заказа"
    assert lead.proposal_price_rub == 12000
    assert lead.proposal_days == 5


def test_initialize_adds_proposal_fields_to_existing_leads_database(tmp_path):
    database_path = tmp_path / "leads.sqlite3"
    with sqlite3.connect(database_path) as conn:
        conn.execute(
            """
            CREATE TABLE leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                summary TEXT NOT NULL,
                draft_reply TEXT NOT NULL,
                contact TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                email_message_id TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    Storage(database_path).initialize()

    with sqlite3.connect(database_path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(leads)")}
    assert {"proposal_title", "proposal_price_rub", "proposal_days"} <= columns


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
    post_text = "📌 Лендинг с формой заявки\nНужно сверстать лендинг HTML/CSS/JS, поправить форму. Контакт @client_dev"
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
    assert storage.get_order(order_id).title == "Лендинг с формой заявки"


def test_initialize_backfills_generated_order_title_from_linked_lead(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=44,
        post_url="https://kwork.ru/projects/44/view",
        text="📌 Исправить форму заявки\nПредложений: 1",
        posted_at="2026-05-04T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=85,
        summary="AI: accept\nЗадача: Исправить форму заявки",
        draft_reply="Здравствуйте! Готов помочь.",
        contact="https://kwork.ru/projects/44/view",
    )
    order_id = storage.create_order(
        lead_id=lead_id,
        contact="https://kwork.ru/projects/44/view",
        title="AI: accept\nСрок: 3 дн.\nЗадача: Исправить форму заявки",
        brief="Текст заказа",
    )

    storage.initialize()

    assert storage.get_order(order_id).title == "Исправить форму заявки"


def test_list_leads_returns_latest_first_with_post_metadata_and_sent_state(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    old_post_id = storage.save_post(
        channel="kwork-web",
        message_id=100,
        post_url="https://kwork.ru/projects/100/view",
        text="📌 Старый заказ\nПредложений: 2",
        posted_at="2026-05-04T09:00:00+03:00",
    )
    new_post_id = storage.save_post(
        channel="kwork-web",
        message_id=101,
        post_url="https://kwork.ru/projects/101/view",
        text="📌 Новый заказ\nПредложений: 1",
        posted_at="2026-05-04T11:00:00+03:00",
    )
    old_lead_id = storage.create_lead(
        post_id=old_post_id,
        score=80,
        summary="Старый",
        draft_reply="Здравствуйте! Сделаю.",
        contact="https://kwork.ru/projects/100/view",
    )
    new_lead_id = storage.create_lead(
        post_id=new_post_id,
        score=90,
        summary="Новый",
        draft_reply="Здравствуйте! Сделаю.",
        contact="https://kwork.ru/projects/101/view",
    )

    storage.mark_sent(old_lead_id, "https://kwork.ru/projects/100/view", "kwork-project-100")

    leads = storage.list_leads()

    assert [lead.id for lead in leads] == [new_lead_id, old_lead_id]
    assert leads[0].channel == "kwork-web"
    assert leads[0].message_id == 101
    assert leads[0].posted_at == "2026-05-04T11:00:00+03:00"
    assert leads[1].status == "sent"
    assert leads[1].sent_at


def test_lead_attachments_are_saved_and_replaced(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=200,
        post_url="https://kwork.ru/projects/200/view",
        text="📌 Заказ с ТЗ\nПредложений: 2",
        posted_at="2026-05-04T10:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=90,
        summary="AI summary",
        draft_reply="Здравствуйте! Сделаю.",
        contact="https://kwork.ru/projects/200/view",
    )

    storage.replace_lead_attachments(
        lead_id,
        [
            LeadAttachment(
                id=0,
                lead_id=lead_id,
                label="ТЗ.zip",
                url="https://kwork.ru/files/tz.zip",
                local_path=str(tmp_path / "attachments" / "tz.zip"),
                status="скачан, архив открыт",
                summary="brief.txt: прочитан",
                kind="archive",
                opened_archive=True,
                ocr_scanned=False,
            )
        ],
    )
    storage.replace_lead_attachments(
        lead_id,
        [
            LeadAttachment(
                id=0,
                lead_id=lead_id,
                label="screen.png",
                url="https://kwork.ru/files/screen.png",
                local_path=str(tmp_path / "attachments" / "screen.png"),
                status="скачан, OCR прочитан",
                summary="На скрине макет формы",
                kind="image",
                opened_archive=False,
                ocr_scanned=True,
            )
        ],
    )

    attachments = storage.list_lead_attachments(lead_id)

    assert len(attachments) == 1
    assert attachments[0].label == "screen.png"
    assert attachments[0].status == "скачан, OCR прочитан"
    assert attachments[0].ocr_scanned is True
    assert attachments[0].opened_archive is False


def test_replace_lead_attachments_deduplicates_same_file_url(tmp_path):
    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    post_id = storage.save_post(
        channel="kwork-web",
        message_id=201,
        post_url="https://kwork.ru/projects/201/view",
        text="Заказ с вложением",
        posted_at="2026-06-03T12:00:00+03:00",
    )
    lead_id = storage.create_lead(
        post_id=post_id,
        score=80,
        summary="AI summary",
        draft_reply="Здравствуйте! Сделаю.",
        contact="https://kwork.ru/projects/201/view",
    )
    attachment = LeadAttachment(
        id=0,
        lead_id=lead_id,
        label="ТЗ.pdf",
        url="https://kwork.ru/files/tz.pdf",
        local_path="C:/tmp/tz.pdf",
        status="скачан, текст прочитан",
        summary="Техническое задание",
        kind="pdf",
        opened_archive=False,
        ocr_scanned=False,
    )

    storage.replace_lead_attachments(lead_id, [attachment, attachment])

    assert [item.url for item in storage.list_lead_attachments(lead_id)] == [attachment.url]


def test_initialize_removes_duplicate_attachment_urls_from_legacy_database(tmp_path):
    database_path = tmp_path / "leads.sqlite3"
    with sqlite3.connect(database_path) as conn:
        conn.execute(
            """
            CREATE TABLE lead_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                url TEXT NOT NULL,
                local_path TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                kind TEXT NOT NULL DEFAULT 'file',
                opened_archive INTEGER NOT NULL DEFAULT 0,
                ocr_scanned INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO lead_attachments (lead_id, label, url, status)
            VALUES (42, 'ТЗ.pdf', 'https://kwork.ru/files/tz.pdf', 'скачан')
            """,
            [(), ()],
        )

    storage = Storage(database_path)
    storage.initialize()

    assert len(storage.list_lead_attachments(42)) == 1

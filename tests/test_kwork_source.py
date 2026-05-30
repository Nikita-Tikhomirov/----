from app.kwork_source import parse_kwork_project_cards


def test_parse_kwork_project_cards_keeps_only_low_offer_projects():
    html = """
    <div class="want-card">
      <a class="want-card__title" href="/projects/3177548/view">Создать сайт на Tilda</a>
      <div class="want-card__description">Нужна помощь с лендингом</div>
      <div class="want-card__informers-row">
        <span>Осталось: 2 д. 17 ч.</span>
        <span>Предложений:&nbsp;4</span>
      </div>
    </div>
    <div class="want-card">
      <a class="want-card__title" href="/projects/3177557/view">Сайт-калькулятор</a>
      <div class="want-card__description">Нужен калькулятор услуг</div>
      <div class="want-card__informers-row">
        <span>Предложений:&nbsp;27</span>
      </div>
    </div>
    """

    posts = parse_kwork_project_cards(html, max_responses=5)

    assert len(posts) == 1
    assert posts[0].channel == "kwork-web"
    assert posts[0].message_id == 3177548
    assert posts[0].url == "https://kwork.ru/projects/3177548/view"
    assert "Предложений: 4" in posts[0].text
    assert "Отклик: https://kwork.ru/projects/3177548/view" in posts[0].text


def test_parse_kwork_project_cards_skips_cards_without_offer_count():
    html = """
    <div class="want-card">
      <a href="/projects/1/view">Без счетчика</a>
    </div>
    """

    assert parse_kwork_project_cards(html, max_responses=5) == []


def test_kwork_web_project_ids_deduplicate_through_storage(tmp_path, monkeypatch):
    from app.main import scan_once
    from app.ai_lead_judge import LeadJudgeResult
    from app.storage import Storage

    judge_calls = []

    def fake_judge(text, api_key="", model="deepseek-chat"):
        judge_calls.append(text)
        return LeadJudgeResult(
            accepted=True,
            decision="accept",
            score=80,
            complexity="simple",
            estimated_days=1,
            price_rub=5000,
            summary="Проект",
            reasons=["подходит"],
            risks=[],
            questions=[],
            draft_reply="AI reply",
        )

    class FakeSource:
        def fetch_recent_posts(self):
            return parse_kwork_project_cards(
                """
                <div class="want-card">
                  <a href="/projects/123/view">Проект</a>
                  <span>Предложений: 1</span>
                </div>
                """,
                max_responses=5,
            )

        def send_message(self, contact, text):
            raise AssertionError("not used")

    class FakeEmail:
        def __init__(self):
            self.sent = []

        def send_lead(self, lead):
            self.sent.append(lead.id)
            return f"<lead-{lead.id}@example.com>"

    storage = Storage(tmp_path / "leads.sqlite3")
    storage.initialize()
    email = FakeEmail()

    assert scan_once(storage, FakeSource(), email, deepseek_api_key="sk-test", lead_judge=fake_judge) == 1
    assert scan_once(storage, FakeSource(), email, deepseek_api_key="sk-test", lead_judge=fake_judge) == 0
    assert len(storage.list_leads()) == 1
    assert email.sent == [1]
    assert len(judge_calls) == 1

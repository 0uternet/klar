import json

from fake_llm import FakeLLM, is_probe, system_text
from klar.checks.base import verdict_schema
from klar.llm import AnswerStore, LLMClient, RequestCounter
from klar.llm.capabilities import CapabilityCache, probe_capabilities
from klar.models import LLMTask

GOOD = {"outcome": "failed", "confidence": "high", "quote": "Mehr", "reason": "Generic.", "fix": "Abfallkalender"}


def task(user: str = 'link text: "Mehr"') -> LLMTask:
    return LLMTask(system="You check WCAG 2.4.4.", user=user, json_schema=verdict_schema(), max_tokens=120)


def client(settings, counter=None, caps=None) -> LLMClient:
    return LLMClient(settings, AnswerStore(settings.replay_path, settings.llm_name), counter or RequestCounter(),
                     capabilities=caps)


def test_request_parameters(make_settings):
    with FakeLLM(lambda r: GOOD) as fake:
        res = client(make_settings(llm_base_url=fake.base_url)).ask(task(), prompt_version="t/v1", criterion="2.4.4")
    assert res.answer == GOOD
    req = fake.requests[0]
    assert req["temperature"] == 0
    assert req["seed"] == 42
    assert req["max_tokens"] == 120
    assert "tools" not in req and "tool_choice" not in req  # never any tools
    assert req["chat_template_kwargs"] == {"enable_thinking": False}  # extra_body is merged into the body
    rf = req["response_format"]
    assert rf["type"] == "json_schema" and rf["json_schema"]["strict"] is True
    assert "default" not in json.dumps(rf["json_schema"]["schema"])
    assert res.tokens_in == 100 and res.tokens_out == 20 and res.requests == 1
    assert res.latency_ms >= 0 and not res.cached


def test_flags_come_from_independent_probes(make_settings):
    """A proxy that rejects only chat_template_kwargs keeps constrained decoding."""
    def responder(req):
        if "chat_template_kwargs" in req:
            return 400, "Unrecognized request argument supplied: chat_template_kwargs"
        if is_probe(req):
            return '{"ok": true}'
        return GOOD

    with FakeLLM(responder) as fake:
        settings = make_settings(llm_base_url=fake.base_url)
        counter = RequestCounter()
        caps = CapabilityCache(settings, counter)
        c = client(settings, counter, caps.get)
        assert c.ask(task(), prompt_version="t/v1", criterion="2.4.4").answer == GOOD
    probe = caps.get()
    assert probe.chat_template_kwargs is False and probe.json_schema is True
    last = fake.requests[-1]
    assert "response_format" in last and "chat_template_kwargs" not in last


def test_json_schema_unsupported_uses_the_prompt_and_tolerant_parsing(make_settings):
    def responder(req):
        if "response_format" in req:
            return 400, "response_format json_schema is not supported"
        if is_probe(req):
            return "ok"
        return "```json\n" + json.dumps(GOOD) + "\n```"

    with FakeLLM(responder) as fake:
        settings = make_settings(llm_base_url=fake.base_url)
        counter = RequestCounter()
        caps = CapabilityCache(settings, counter)
        c = client(settings, counter, caps.get)
        assert c.ask(task(), prompt_version="t/v1", criterion="2.4.4").answer == GOOD
        assert c.schema_level == "json_prompt"
    last = fake.requests[-1]
    assert "response_format" not in last
    assert "JSON schema" in system_text(last)  # the schema goes into the prompt instead


def test_a_mid_scan_400_is_a_failed_question_not_a_silent_downgrade(make_settings):
    with FakeLLM(lambda r: (400, "bad request")) as fake:
        c = client(make_settings(llm_base_url=fake.base_url))
        res = c.ask(task(), prompt_version="t/v1", criterion="2.4.4")
        assert res.answer is None and res.error_kind == "request_failed"
        assert c.schema_level == "json_schema"  # unchanged
        c.ask(task("again"), prompt_version="t/v1", criterion="2.4.4")
    assert all("response_format" in r for r in fake.requests)


def test_one_retry_with_the_validation_error(make_settings):
    answers = iter(['{"outcome": "probably"}', json.dumps(GOOD)])
    with FakeLLM(lambda r: next(answers)) as fake:
        res = client(make_settings(llm_base_url=fake.base_url)).ask(task(), prompt_version="t/v1", criterion="2.4.4")
    assert res.answer == GOOD
    assert res.requests == 2
    retry = fake.requests[1]["messages"]
    assert retry[-2]["role"] == "assistant" and retry[-1]["role"] == "user"
    assert "not valid" in retry[-1]["content"] and "missing field" in retry[-1]["content"]


def test_unparseable_after_retry(make_settings):
    with FakeLLM(lambda r: "I think it fails.") as fake:
        res = client(make_settings(llm_base_url=fake.base_url)).ask(task(), prompt_version="t/v1", criterion="2.4.4")
    assert res.answer is None and res.error_kind == "unparseable" and res.requests == 2


def test_request_failed_does_not_raise(make_settings):
    fake = FakeLLM()
    url = fake.base_url
    fake.server.server_close()  # nothing listens on that port any more
    res = client(make_settings(llm_base_url=url, llm_timeout=2)).ask(task(), prompt_version="t/v1", criterion="2.4.4")
    assert res.answer is None and res.error_kind == "request_failed"


def test_requests_are_counted_by_destination(make_settings, tmp_path):
    with FakeLLM(lambda r: GOOD) as fake:
        local = RequestCounter()
        client(make_settings(llm_base_url=fake.base_url), local).ask(task(), prompt_version="t/v1", criterion="2.4.4")
        swiss = RequestCounter()
        s = make_settings(llm_base_url=fake.base_url, mode_override="swiss_cloud", replay_dir=tmp_path / "r2")
        client(s, swiss).ask(task(), prompt_version="t/v1", criterion="2.4.4")
    assert local.by_class == {"local": 1, "swiss_cloud": 0, "external": 0} and local.value == 0
    assert swiss.by_class["swiss_cloud"] == 1 and swiss.value == 1


def test_recorded_answers_carry_provenance(make_settings):
    with FakeLLM(lambda r: GOOD) as fake:
        s = make_settings(llm_base_url=fake.base_url)
        client(s).ask(task(), prompt_version="t/v1", criterion="2.4.4")
    rec = json.loads(next(s.replay_path.glob("*.jsonl")).read_text(encoding="utf-8").splitlines()[0])
    assert rec["endpoint_host"] == "127.0.0.1" and rec["mode"] == "local" and rec["klar_version"]
    assert rec["decoding"] == {"temperature": 0, "seed": 42, "max_tokens": 120, "schema_level": "json_schema",
                               "thinking": "disabled"}


def test_vision_probe_uses_models_endpoint_first(make_settings):
    with FakeLLM(lambda r: "red", modalities=["text"]) as fake:
        caps = probe_capabilities(make_settings(llm_base_url=fake.base_url, vision_override=None), RequestCounter())
    assert caps.vision is False and caps.source == "probe" and "input_modalities" in caps.detail
    assert not any(isinstance(r["messages"][0]["content"], list) for r in fake.requests)  # no image sent


def test_vision_probe_checks_the_answer(make_settings):
    with FakeLLM(lambda r: "Red.") as fake:
        caps = probe_capabilities(make_settings(llm_base_url=fake.base_url, vision_override=None), RequestCounter())
    assert caps.vision is True and caps.source == "probe"
    image_requests = [r for r in fake.requests if isinstance(r["messages"][0]["content"], list)]
    assert image_requests[0]["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    with FakeLLM(lambda r: "blue") as fake:  # a proxy that drops images and answers anyway
        caps = probe_capabilities(make_settings(llm_base_url=fake.base_url, vision_override=None), RequestCounter())
    assert caps.vision is False and caps.source == "probe"


def test_vision_probe_error_means_no_vision(make_settings):
    def responder(req):
        if isinstance(req["messages"][0]["content"], list):
            return 400, "image input is not supported"
        return "ok"

    with FakeLLM(responder) as fake:
        caps = probe_capabilities(make_settings(llm_base_url=fake.base_url, vision_override=None), RequestCounter())
    assert caps.vision is False and caps.source == "error"


def test_replay_mode_vision_and_override(make_settings):
    assert probe_capabilities(make_settings(replay=True, vision_override=None), RequestCounter()).vision is False  # nothing recorded
    assert probe_capabilities(make_settings(replay=True, vision_override=False), RequestCounter()).source == "override"

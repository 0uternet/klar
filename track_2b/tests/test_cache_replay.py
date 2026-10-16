import json

from fake_llm import FakeLLM
from klar.checks.base import verdict_schema
from klar.llm import AnswerStore, LLMClient, ReplayClient, RequestCounter, make_backend
from klar.llm.cache import keys_for, model_slug
from klar.models import LLMTask

ANSWER = {"outcome": "passed", "confidence": "high", "quote": "Mehr", "reason": "Clear.", "fix": ""}


def task(images=None, user="u") -> LLMTask:
    return LLMTask(system="s", user=user, json_schema=verdict_schema(), images=images or [])


def test_keys_are_content_addressed(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "x.png").write_bytes(b"PNG1")
    (tmp_path / "b" / "y.png").write_bytes(b"PNG1")
    k1 = keys_for("m", "v1", task(["a/x.png"]), tmp_path)
    k2 = keys_for("m", "v1", task(["b/y.png"]), tmp_path)
    assert k1 == k2  # same bytes, different path → same key
    assert keys_for("m", "v2", task(["a/x.png"]), tmp_path)["key"] != k1["key"]  # prompt_version
    km = keys_for("other", "v1", task(["a/x.png"]), tmp_path)
    assert km["key"] != k1["key"] and km["task_key"] == k1["task_key"]  # model only in the exact key
    (tmp_path / "b" / "y.png").write_bytes(b"PNG2")
    k3 = keys_for("m", "v1", task(["b/y.png"]), tmp_path)
    assert k3["key"] != k1["key"] and k3["loose_key"] == k1["loose_key"]


def test_context_shown_is_not_part_of_the_key(tmp_path):
    a = LLMTask(system="s", user="u", json_schema={}, context_shown={"x": "1"})
    b = LLMTask(system="s", user="u", json_schema={}, context_shown={"x": "2"})
    assert keys_for("m", "v", a, tmp_path) == keys_for("m", "v", b, tmp_path)


def test_live_records_then_replay_without_network(make_settings):
    with FakeLLM(lambda r: ANSWER) as fake:
        live_settings = make_settings(llm_base_url=fake.base_url)
        live = make_backend(live_settings, RequestCounter())
        assert isinstance(live, LLMClient)
        assert live.ask(task(), prompt_version="v1", criterion="2.4.4").answer == ANSWER
        # same question again: served from the cache, no HTTP request
        again = live.ask(task(), prompt_version="v1", criterion="2.4.4")
        assert again.cached and again.requests == 0
        assert len(fake.requests) == 1
    path = live_settings.replay_path / f"{model_slug(live_settings.llm_name)}.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["answer"] == ANSWER

    # the server is gone: replay mode must answer from the JSONL alone
    replay = make_backend(make_settings(replay=True), RequestCounter())
    assert isinstance(replay, ReplayClient)
    res = replay.ask(task(), prompt_version="v1", criterion="2.4.4")
    assert res.answer == ANSWER and res.cached and res.requests == 0
    miss = replay.ask(task(user="never asked"), prompt_version="v1", criterion="2.4.4")
    assert miss.answer is None and miss.error_kind == "not_recorded"


def test_replay_falls_back_to_other_model_recordings(make_settings, tmp_path):
    s = make_settings(replay=True)
    store = AnswerStore(s.replay_path, "swiss-ai/Apertus-v1.5-70B")
    keys = keys_for("swiss-ai/Apertus-v1.5-70B", "v1", task(), None)
    store.put(keys, prompt_version="v1", criterion="2.4.4", answer=ANSWER, raw=None, tokens_in=1, tokens_out=1, latency_ms=1)
    replay = make_backend(s, RequestCounter())  # model = 8B
    assert replay.ask(task(), prompt_version="v1", criterion="2.4.4").answer == ANSWER


def test_store_skips_corrupt_lines(tmp_path):
    (tmp_path / "m.jsonl").write_text('not json\n{"key": "k", "answer": {"a": 1}}\n', encoding="utf-8")
    store = AnswerStore(tmp_path, "m")
    assert store.get({"key": "k", "task_key": "", "loose_key": ""}) == {"key": "k", "answer": {"a": 1}}


def test_first_recorded_answer_wins_for_a_repeated_question(tmp_path):
    # A later re-ask of the same question (e.g. the -context ablation) must not replace the
    # answer the main run used, or a replay would not reproduce that run.
    (tmp_path / "m.jsonl").write_text('{"key": "k", "answer": {"a": 1}}\n{"key": "k", "answer": {"a": 2}}\n', encoding="utf-8")
    store = AnswerStore(tmp_path, "m")
    assert store.get({"key": "k", "task_key": "", "loose_key": ""})["answer"] == {"a": 1}


def test_replay_store_is_read_only(make_settings):
    s = make_settings(replay=True)
    backend = make_backend(s, RequestCounter())
    assert backend.store.writable is False


def test_replay_serves_only_allow_listed_models(make_settings):
    """A comparison model's recording can never be replayed as if it were Apertus."""
    s = make_settings(replay=True)
    other = AnswerStore(s.replay_path, "meta-llama/Llama-3.1-8B-Instruct")
    other.put(keys_for("meta-llama/Llama-3.1-8B-Instruct", "v1", task(), None), prompt_version="v1",
              criterion="2.4.4", answer=ANSWER, raw=None, tokens_in=1, tokens_out=1, latency_ms=1)
    replay = make_backend(s, RequestCounter())
    res = replay.ask(task(), prompt_version="v1", criterion="2.4.4")
    assert res.answer is None and res.error_kind == "not_recorded"
    assert "meta-llama/Llama-3.1-8B-Instruct" in replay.store.ignored_models


def test_exact_replay_refuses_approximate_matches(make_settings):
    s = make_settings(replay=True)
    store = AnswerStore(s.replay_path, "swiss-ai/Apertus-v1.5-70B")
    store.put(keys_for("swiss-ai/Apertus-v1.5-70B", "v1", task(), None), prompt_version="v1", criterion="2.4.4",
              answer=ANSWER, raw=None, tokens_in=1, tokens_out=1, latency_ms=1, provenance={"endpoint_host": "h"})
    loose = make_backend(s, RequestCounter())
    assert loose.model == "swiss-ai/Apertus-v1.5-70B"  # replays what was recorded, and says so
    assert loose.ask(task(), prompt_version="v1", criterion="2.4.4").match == "exact"
    s8 = s.with_(llm_name="swiss-ai/Apertus-v1.5-8B")
    store8 = AnswerStore(s.replay_path, "swiss-ai/Apertus-v1.5-8B")
    store8.put(keys_for("swiss-ai/Apertus-v1.5-8B", "v1", task(user="x"), None), prompt_version="v1",
               criterion="2.4.4", answer=ANSWER, raw=None, tokens_in=1, tokens_out=1, latency_ms=1)
    approx = make_backend(s8, RequestCounter())
    assert approx.ask(task(), prompt_version="v1", criterion="2.4.4").match == "task"  # 70B answer, 8B key
    exact = make_backend(s8.with_(replay_exact=True), RequestCounter())
    assert exact.ask(task(), prompt_version="v1", criterion="2.4.4").error_kind == "not_recorded"
    assert exact.store.summary()["hosts"] == ["h"]


def test_replay_vision_only_when_vision_answers_were_recorded(make_settings):
    from klar.llm.capabilities import probe_capabilities

    s = make_settings(replay=True, vision_override=None)
    assert probe_capabilities(s, RequestCounter()).vision is False
    store = AnswerStore(s.replay_path, s.llm_name)
    # text-only answers, even for a vision criterion, do not make replay "see"
    store.put(keys_for(s.llm_name, "1.1.1/v2", task(), None), prompt_version="1.1.1/v2", criterion="1.1.1",
              answer=ANSWER, raw=None, tokens_in=1, tokens_out=1, latency_ms=1, provenance={"has_image": False})
    store.put(keys_for(s.llm_name, "2.4.4/v3", task(user="t"), None), prompt_version="2.4.4/v3", criterion="2.4.4",
              answer=ANSWER, raw=None, tokens_in=1, tokens_out=1, latency_ms=1)
    assert probe_capabilities(s, RequestCounter()).vision is False
    store.put(keys_for(s.llm_name, "1.1.1/v2", task(user="img"), None), prompt_version="1.1.1/v2", criterion="1.1.1",
              answer=ANSWER, raw=None, tokens_in=1, tokens_out=1, latency_ms=1, provenance={"has_image": True})
    caps = probe_capabilities(s, RequestCounter())
    assert caps.vision is True and caps.source == "replay"


def test_live_recordings_say_whether_an_image_was_sent(make_settings, tmp_path):
    import json

    from fake_llm import FakeLLM
    from klar.llm import LLMClient

    (tmp_path / "crops").mkdir()
    (tmp_path / "crops" / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    with FakeLLM(lambda r: ANSWER) as fake:
        s = make_settings(llm_base_url=fake.base_url)
        c = LLMClient(s, AnswerStore(s.replay_path, s.llm_name), RequestCounter())
        c.ask(task(), prompt_version="v1", criterion="2.4.4")
        c.ask(task(images=["crops/a.png"]), prompt_version="v1", criterion="1.1.1", image_root=tmp_path)
    recs = [json.loads(x) for x in next(s.replay_path.glob("*.jsonl")).read_text(encoding="utf-8").splitlines()]
    assert [r["has_image"] for r in recs] == [False, True]


def test_cache_and_replay_hits_are_free(make_settings):
    """Only questions that reach the endpoint count against KLAR_MAX_LLM_CALLS."""
    with FakeLLM(lambda r: ANSWER) as fake:
        live_settings = make_settings(llm_base_url=fake.base_url)
        live = make_backend(live_settings, RequestCounter())
        q = task(user="free after the first answer")
        assert not live.is_free(q, prompt_version="v1")
        live.ask(q, prompt_version="v1", criterion="2.4.4")
        assert live.is_free(q, prompt_version="v1") and not live.is_free(q, prompt_version="v2")
    replay = make_backend(make_settings(replay=True), RequestCounter())
    assert replay.is_free(q, prompt_version="v1")
    assert not replay.is_free(task(user="never recorded"), prompt_version="v1")

import pytest

from klar.config import Settings, detect_mode


@pytest.mark.parametrize("url, mode", [
    (None, "replay"),
    ("", "replay"),
    ("http://llm-gpu:8000/v1", "local"),
    ("http://llm-cpu:8080/v1", "local"),
    ("http://llm:8000/v1", "local"),
    ("http://localhost:8000/v1", "local"),
    ("http://127.0.0.1:8081/v1", "local"),
    ("http://[::1]:8000/v1", "local"),
    ("http://10.0.0.12:8000/v1", "local"),
    ("http://192.168.1.20/v1", "local"),
    ("http://172.16.4.2/v1", "local"),
    ("http://vllm:8000/v1", "local"),  # dot-less docker/LAN service name
    ("https://maas.phoeniqs.com/v1", "swiss_cloud"),
    ("https://api.inference.cscs.ch/v1", "swiss_cloud"),
    ("https://cscs.ch/v1", "swiss_cloud"),
    ("https://evilphoeniqs.com/v1", "external"),  # suffix must match on a label boundary
    ("https://phoeniqs.com.attacker.io/v1", "external"),
    ("https://api.openai.com/v1", "external"),
    ("http://8.8.8.8/v1", "external"),
])
def test_detect_mode(url, mode):
    assert detect_mode(url, replay_flag=False) == mode


def test_replay_flag_wins_over_local_endpoint():
    assert detect_mode("http://llm-gpu:8000/v1", replay_flag=True) == "replay"


def test_from_env_defaults_to_replay_without_base_url(tmp_path):
    s = Settings.from_env({"KLAR_DATA_DIR": str(tmp_path)})
    assert s.mode == "replay"
    assert s.llm_name == "swiss-ai/Apertus-v1.5-8B"
    assert s.counts_external_requests is False
    assert s.data_dir == tmp_path.resolve()


def test_from_env_reads_template_variables():
    s = Settings.from_env({"LLM_BASE_URL": "https://maas.phoeniqs.com/v1", "LLM_NAME": "inference-apertus-v15-70b",
                           "LLM_API_KEY": "secret", "KLAR_UI_LANG": "fr", "KLAR_VISION": "0"})
    assert s.mode == "swiss_cloud"
    assert s.provider == "Phoeniqs"
    assert s.base_url_host == "maas.phoeniqs.com"
    assert s.ui_lang == "fr"
    assert s.vision_override is False
    assert s.counts_external_requests is True


def test_from_env_replay_flag():
    s = Settings.from_env({"LLM_BASE_URL": "http://localhost:8000/v1", "KLAR_REPLAY": "1"})
    assert s.mode == "replay"


def test_invalid_ui_lang_falls_back_to_english():
    assert Settings.from_env({"KLAR_UI_LANG": "es"}).ui_lang == "en"

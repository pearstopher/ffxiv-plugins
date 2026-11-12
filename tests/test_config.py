import json

import pytest

from scripts.config import CONFIG_PATH, Config, load_config


def write(tmp_path, data):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_defaults_fill_missing_fields(tmp_path):
    assert load_config(write(tmp_path, {"owner": "me"})) == Config(owner="me")


def test_lists_become_tuples(tmp_path):
    config = load_config(write(tmp_path, {"owner": "me", "include": ["a"], "exclude": ["b"]}))
    assert config.include == ("a",)
    assert config.exclude == ("b",)


def test_unknown_key_is_an_error(tmp_path):
    with pytest.raises(TypeError):
        load_config(write(tmp_path, {"owner": "me", "typo": 1}))


def test_repo_config_loads():
    assert load_config(CONFIG_PATH).owner == "pearstopher"

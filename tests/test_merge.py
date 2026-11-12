import json

from scripts.merge import merge, needs_write, read_json, to_json, version_key, write_json


def entry(name, version, **extra):
    return {"InternalName": name, "AssemblyVersion": version, **extra}


def test_version_key_compares_numerically():
    assert version_key("1.10.0.0") > version_key("1.9.0.0")
    assert version_key("2.0") > version_key("1.99.99.99")
    assert version_key("1.0-beta") == (1, 0)


def test_duplicate_keeps_highest_version():
    old, new = entry("A", "1.9.0.0"), entry("A", "1.10.0.0")
    assert merge([new, old]) == [new]
    assert merge([old, new]) == [new]


def test_equal_versions_keep_first_seen():
    first, second = entry("A", "1.0.0.0", src=1), entry("A", "1.0.0.0", src=2)
    assert merge([first, second]) == [first]


def test_sorted_by_name_case_insensitively():
    entries = [entry("charlie", "1"), entry("Bravo", "1"), entry("alpha", "1")]
    assert [e["InternalName"] for e in merge(entries)] == ["alpha", "Bravo", "charlie"]


def test_output_is_deterministic_regardless_of_input_order():
    entries = [entry("B", "1"), entry("A", "2"), entry("A", "1")]
    assert to_json(merge(entries)) == to_json(merge(list(reversed(entries))))


def test_json_format():
    data = to_json([entry("Á", "1")])
    assert data.endswith(b"]\n")
    assert b"\r" not in data
    assert "Á".encode() in data  # not \u-escaped
    assert json.loads(data) == [entry("Á", "1")]


def test_write_and_read_round_trip_with_lf(tmp_path):
    path = tmp_path / "pluginmaster.json"
    entries = [entry("A", "1", Description="line one\nline two")]

    assert read_json(path) == []
    write_json(entries, path)
    assert b"\r" not in path.read_bytes()
    assert read_json(path) == entries


def test_needs_write_detects_changes(tmp_path):
    path = tmp_path / "pluginmaster.json"
    entries = [entry("A", "1")]

    assert needs_write(entries, path)  # missing file
    write_json(entries, path)
    assert not needs_write(entries, path)
    assert needs_write([entry("A", "2")], path)


def test_needs_write_flags_crlf_copy(tmp_path):
    path = tmp_path / "pluginmaster.json"
    entries = [entry("A", "1")]
    path.write_bytes(to_json(entries).replace(b"\n", b"\r\n"))
    assert needs_write(entries, path)

"""End-to-end realistic config parsing."""

from __future__ import annotations

from datetime import date

import tomlmini


SAMPLE = """
# Demo configuration

title = "Forge Pipeline"

[owner]
name = "Forge Team"
since = 2024-01-15

[database]
host = "db.internal"
port = 5432
enabled = true
options = { pool = 16, timeout = 30.0 }

[[servers]]
name = "alpha"
ip = "10.0.0.1"
roles = ["web", "api"]

[[servers]]
name = "beta"
ip = "10.0.0.2"
roles = ["worker"]

[servers.health]
ok = true

[paths]
log_dir = '/var/log/forge'
data_dir = """ + "\"\"\"" + r"""
/var
/data
""" + "\"\"\"" + r"""
"""


def test_realistic_config_parses_into_expected_dict() -> None:
    parsed = tomlmini.loads(SAMPLE)

    assert parsed["title"] == "Forge Pipeline"
    assert parsed["owner"] == {"name": "Forge Team", "since": date(2024, 1, 15)}

    assert parsed["database"]["host"] == "db.internal"
    assert parsed["database"]["port"] == 5432
    assert parsed["database"]["enabled"] is True
    assert parsed["database"]["options"] == {"pool": 16, "timeout": 30.0}

    assert len(parsed["servers"]) == 2
    assert parsed["servers"][0]["name"] == "alpha"
    assert parsed["servers"][0]["roles"] == ["web", "api"]
    assert parsed["servers"][1]["name"] == "beta"
    # The [servers.health] header attaches to the most recently declared
    # array element, matching TOML 1.0.
    assert parsed["servers"][-1]["health"] == {"ok": True}

    assert parsed["paths"]["log_dir"] == "/var/log/forge"
    assert parsed["paths"]["data_dir"] == "/var\n/data\n"


def test_round_trip_via_file(tmp_path) -> None:
    p = tmp_path / "demo.toml"
    p.write_text(SAMPLE, encoding="utf-8")
    direct = tomlmini.loads(SAMPLE)
    via_file = tomlmini.load(p)
    assert direct == via_file

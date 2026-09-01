"""Tests for structured usage logging."""

import json

from medical_mcps.usage_logging import log_tool_call


def test_log_tool_call_writes_json_line(capsys):
    log_tool_call(
        tool="pubmed_search_articles",
        arguments={"query": "diabetes", "limit": 10},
        outcome="ok",
        latency_ms=12.3,
    )

    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    assert payload["event"] == "tool_call"
    assert payload["tool"] == "pubmed_search_articles"
    assert payload["args_keys"] == ["limit", "query"]
    assert payload["arg_count"] == 2
    assert payload["outcome"] == "ok"
    assert payload["latency_ms"] == 12.3
    assert "diabetes" not in out

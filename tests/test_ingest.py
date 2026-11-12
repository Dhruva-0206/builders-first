from builders_first.ingest_ecosystems import repo_key
from builders_first.ingest_hackathon import parse_github


def test_repo_key():
    assert repo_key("https://github.com/Near/NearCore") == "near/nearcore"
    assert repo_key("https://github.com/a/b.git") == "a/b"
    assert repo_key("https://gitlab.com/a/b") is None


def test_parse_github():
    assert parse_github("https://github.com/Owner/Repo/tree/main") == ("Owner", "Repo")
    assert parse_github("https://www.github.com/o/r.git") == ("o", "r")
    assert parse_github("https://github.com/orgs/foo") is None
    assert parse_github("") is None
    assert parse_github("https://example.com") is None


def test_ai_match():
    from builders_first.ingest_github import ai_match, is_bot

    assert ai_match("fix\n\nCo-Authored-By: Claude <noreply@anthropic.com>") == "claude"
    assert ai_match("x\nco-authored-by: Copilot <x@github.com>") == "copilot"
    assert ai_match("🤖 Generated with [Claude Code](https://claude.com)") == "claude"
    assert ai_match("Co-authored-by: Alice <a@b.c>") == ""
    assert ai_match("") == ""
    assert is_bot("dependabot[bot]") and is_bot("deploy-bot") and not is_bot("alice")

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def test_connector_attribution_is_disclosed_before_sending() -> None:
    skill = (PLUGIN_ROOT / "skills" / "slack-messaging" / "SKILL.md").read_text()

    assert "sender attribution" in skill
    assert "stop and ask the user to choose" in skill
    assert "Do not call the send or schedule tool until they choose" in skill
    assert "as me" in skill
    assert "paste or send it directly in Slack" in skill
    assert "do not promise that a later edit can remove" in skill


def test_connector_attribution_preflight_does_not_block_drafts() -> None:
    skill = (PLUGIN_ROOT / "skills" / "slack-messaging" / "SKILL.md").read_text()

    attribution = skill.split("## Connector Attribution", 1)[1].split("## Formatting", 1)[0]
    assert "only immediately before a real post or scheduled post" in attribution
    assert "compose-only or rewrite-only work" in attribution
    assert "`slack_send_message_draft`" in attribution
    assert "those actions do not send" in attribution

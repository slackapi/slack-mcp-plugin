import time
from typing import TypedDict

import pytest
from deepeval.models import GeminiModel
from deepeval.test_case import ToolCall
from pydantic import BaseModel

from tests.config import GEMINI_API_KEY_POOL, SLACK_MCP_TOKEN
from tests.support.judge import make_judge_model
from tests.support.tools import get_all_skill_tools, get_slack_mcp_tools


class Scenario(TypedDict):
    id: str
    prompt: str
    accepted_tools: list[str]


class ToolChoice(BaseModel):
    """Structured output: the single tool the model picks for a request."""

    tool_name: str


SCENARIOS: list[Scenario] = [
    {
        "id": "send-message-hello-team",
        "prompt": "Send a message saying 'hello team' to the #general channel",
        "accepted_tools": ["slack_send_message"],
    },
    {
        "id": "read-channel-engineering",
        "prompt": "Read the last 10 messages in the #engineering channel",
        "accepted_tools": ["slack_read_channel"],
    },
    {
        "id": "search-deployment-incident",
        "prompt": "Search public channels for messages about the deployment incident last week",
        "accepted_tools": ["slack_search_public"],
    },
    {
        "id": "search-channels-mobile",
        "prompt": "Find which channels are about the mobile project",
        "accepted_tools": ["slack_search_channels"],
    },
    {
        "id": "read-profile-user",
        "prompt": "Look up the profile of user U1234567890",
        "accepted_tools": ["slack_read_user_profile"],
    },
    {
        "id": "list-members-platform-team",
        "prompt": "Who are the members of the #platform-team channel?",
        "accepted_tools": ["slack_list_channel_members"],
    },
    {
        "id": "send-message-release-shipped",
        "prompt": "Let the team in #releases know that v2.1 shipped today",
        "accepted_tools": ["slack_send_message"],
    },
    {
        "id": "search-api-migration",
        "prompt": "Search our public channels for what the team has discussed about the API migration",
        "accepted_tools": ["slack_search_public"],
    },
    {
        "id": "search-channels-design-system",
        "prompt": "Which channels should I join to follow the design system work?",
        "accepted_tools": ["slack_search_channels"],
    },
    {
        "id": "skill-slack-cli-socket-mode",
        "prompt": "Search the Slack developer documentation for how to use socket mode",
        "accepted_tools": ["slack-cli"],
    },
    {
        "id": "skill-block-kit-modal",
        "prompt": "Build a Slack modal dialog with a dropdown menu and a date picker",
        "accepted_tools": ["block-kit"],
    },
    {
        "id": "skill-create-app-template",
        "prompt": "Create a new Slack app project with a slash command from a template",
        "accepted_tools": ["create-slack-app"],
    },
    {
        "id": "ambiguous-post-message-deploy",
        "prompt": "Post a message in #general announcing that the deploy just finished",
        "accepted_tools": ["slack_send_message"],
    },
    {
        "id": "ambiguous-list-members-platform",
        "prompt": "List the members of the #platform-team channel",
        "accepted_tools": ["slack_list_channel_members"],
    },
    {
        "id": "ambiguous-pull-history-engineering",
        "prompt": "Pull the recent message history from the #engineering channel",
        "accepted_tools": ["slack_read_channel"],
    },
    {
        "id": "ambiguous-user-info-profile",
        "prompt": "Fetch the profile details for user U1234567890",
        "accepted_tools": ["slack_read_user_profile"],
    },
    {
        "id": "ambiguous-add-reaction-releases",
        "prompt": "Add a :tada: reaction to the latest message in #releases",
        "accepted_tools": ["slack_add_reaction", "slack_read_channel", "slack_search_public", "slack_search_channels"],
    },
    {
        "id": "ambiguous-reply-in-thread",
        "prompt": "Reply 'we're on it' in the thread on the outage message in #incidents",
        "accepted_tools": ["slack_send_message", "slack_read_thread", "slack_search_public", "slack_search_channels"],
    },
    {
        "id": "ambiguous-read-thread-replies",
        "prompt": "Show me all the replies in the thread on the latest message in #support",
        "accepted_tools": ["slack_read_thread", "slack_read_channel", "slack_search_public", "slack_search_channels"],
    },
    {
        "id": "ambiguous-lookup-user-by-email",
        "prompt": "Find the Slack user with the email jane@example.com",
        "accepted_tools": ["slack_search_users"],
    },
    {
        "id": "ambiguous-schedule-message-standup",
        "prompt": "Schedule a message in #standup for tomorrow at 9am",
        "accepted_tools": ["slack_schedule_message"],
    },
    {
        "id": "skill-slack-api-scopes",
        "prompt": "What OAuth scopes does the chat.postMessage method require?",
        "accepted_tools": ["slack-api"],
    },
    {
        "id": "skill-slack-api-which-method-topic",
        "prompt": "Which Slack Web API method sets a channel's topic, and what scope does it need?",
        "accepted_tools": ["slack-api"],
    },
    {
        "id": "skill-slack-api-pagination",
        "prompt": "How do I handle next_cursor pagination when calling conversations.list?",
        "accepted_tools": ["slack-api"],
    },
    {
        "id": "skill-slack-api-missing-scope",
        "prompt": "A call to users.info is returning a missing_scope error, what scope do I need to add?",
        "accepted_tools": ["slack-api"],
    },
    {
        "id": "skill-slack-api-docs-url",
        "prompt": "What arguments does https://docs.slack.dev/reference/methods/conversations.history take?",
        "accepted_tools": ["slack-api"],
    },
    {
        "id": "skill-slack-api-rate-limit",
        "prompt": "I'm getting a ratelimited error with a Retry-After header on chat.update, how should I back off?",
        "accepted_tools": ["slack-api"],
    },
    {
        "id": "skill-slack-api-call-with-curl",
        "prompt": "How do I call the conversations.history endpoint with curl?",
        "accepted_tools": ["slack-api"],
    },
]


def build_prompt(available_tools: list[ToolCall], prompt: str) -> str:
    tools_list = "\n".join(f"- {t.name}: {t.description}" for t in available_tools)
    return f"""\
You have access to the following tools:

{tools_list}

User request: {prompt}

Pick the single tool that performs the action the user is asking for. Any channel name,
channel ID, or user ID already in the request is usable as-is. Do not pick a search tool
just to resolve it into an ID first. Respond with the tool's exact name."""


class TestToolSelection:
    """Assert the model selects the expected tool for each scenario."""

    model: GeminiModel
    available_tools: list[ToolCall]

    @classmethod
    def setup_class(cls) -> None:
        if not GEMINI_API_KEY_POOL:
            pytest.fail("No Gemini API key set (set GEMINI_API_KEY or GEMINI_API_KEY_*)")
        if not SLACK_MCP_TOKEN:
            pytest.fail("SLACK_MCP_TOKEN not set")
        # Fetch tools once for the whole class: the MCP list is one network
        # round-trip, and skills are read from disk.
        cls.available_tools = get_slack_mcp_tools() + get_all_skill_tools()

    def setup_method(self) -> None:
        self.model = make_judge_model()

    def teardown_method(self) -> None:
        # Gemini's free tier allows only 15 requests/minute. Each scenario makes one
        # model.generate() call, so sleep between scenarios to stay well under the
        # limit (~12 req/min) and avoid HTTP 429 / RESOURCE_EXHAUSTED.
        time.sleep(5)

    @pytest.mark.parametrize(
        "scenario",
        SCENARIOS,
        ids=[s["id"] for s in SCENARIOS],
    )
    def test_tool_selection(self, scenario: Scenario) -> None:
        accepted_tools = scenario["accepted_tools"]
        available_names = {t.name for t in self.available_tools}
        for accepted_tool in accepted_tools:
            assert accepted_tool in available_names, f"Tool {accepted_tool} not found in available tools"

        # Ask the model which tool it would use, then score its actual pick
        # against the accepted set.
        choice, _ = self.model.generate(build_prompt(self.available_tools, scenario["prompt"]), schema=ToolChoice)

        assert choice.tool_name in accepted_tools, (
            f"Expected one of {sorted(accepted_tools)} for prompt {scenario['prompt']!r}, got {choice.tool_name!r}"
        )

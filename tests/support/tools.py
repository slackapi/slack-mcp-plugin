"""Expose plugin skills and Slack MCP tools as comparable `ToolCall` objects."""

import asyncio

from deepeval.test_case import ToolCall
from mcp import ClientSession, types
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client

from tests.config import SLACK_MCP_TOKEN, SLACK_MCP_URL
from tests.skill import discover_skills

__all__ = ["get_all_skill_tools", "get_slack_mcp_tools"]

_CLIENT_INFO = types.Implementation(name="slack-skills-tests", version="0.0.0")


def get_all_skill_tools() -> list[ToolCall]:
    """Convert every discovered plugin skill into a `ToolCall`."""
    return [
        ToolCall(name=skill.frontmatter.name, description=skill.frontmatter.description) for skill in discover_skills()
    ]


async def _list_slack_mcp_tools() -> list[types.Tool]:
    """Open a Streamable HTTP session to the Slack MCP server and page through its tools."""
    headers = {"Authorization": f"Bearer {SLACK_MCP_TOKEN}"}
    async with (
        create_mcp_http_client(headers=headers) as http_client,
        streamable_http_client(SLACK_MCP_URL, http_client=http_client) as (read, write, _),
        ClientSession(read, write, client_info=_CLIENT_INFO) as session,
    ):
        await session.initialize()
        tools: list[types.Tool] = []
        cursor: str | None = None
        while True:
            result = await session.list_tools(params=types.PaginatedRequestParams(cursor=cursor))
            tools.extend(result.tools)
            cursor = result.nextCursor
            if not cursor:
                return tools


def get_slack_mcp_tools() -> list[ToolCall]:
    """Fetch the Slack MCP server's tools and adapt them into `ToolCall` objects."""
    tools = asyncio.run(_list_slack_mcp_tools())
    return [ToolCall(name=tool.name, description=tool.description or "") for tool in tools]

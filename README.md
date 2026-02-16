# Slack MCP Server for Cursor

This repository contains the configuration needed to integrate the Slack Model Context Protocol (MCP) server with Cursor IDE. The MCP enables your agents to interact directly with your Slack workspace, allowing you to search messages, send communications, manage canvases, and more—all through natural language.

## Features

The Slack MCP server provides the following capabilities:

- **Search**: Find messages, files, users, and channels (both public and private)
- **Messaging**: Send messages, retrieve channel histories, and access threaded conversations
- **Canvas**: Create and share formatted documents, export content as markdown
- **User Management**: Retrieve user profiles including custom fields and status information

## Prerequisites

Before setting up the Slack MCP server, ensure you have:

- Cursor IDE installed
- Access to a Slack workspace with MCP integration approved by your workspace admin

## Installation Instructions for Cursor

Follow these steps to configure the Slack MCP server in Cursor:

### Step 1: Open Cursor Settings

Navigate to **Cursor → Settings → Cursor Settings** (or use the keyboard shortcut `Cmd+,` on macOS, `Ctrl+,` on Windows/Linux).

### Step 2: Navigate to MCP Tab

In the Settings interface, click on the **MCP** tab to access MCP server configurations.

### Step 3: Add Slack MCP Configuration

Add the following configuration to connect to the remote Slack MCP server:

```json
{
  "mcpServers": {
    "slack": {
      "url": "https://mcp.slack.com/mcp",
      "auth": {
        "CLIENT_ID": "3660753192626.8903469228982"
      }
    }
  }
}
```

Save the configuration and restart Cursor if prompted.

## Usage Examples

Once configured, you can interact with Slack through your LLMs in Cursor using natural language:

- **Search messages**: "Search for messages about the product launch in the last week"
- **Send messages**: "Send a message to #general channel saying the deployment is complete"
- **Find users**: "Who is the user with email john@example.com?"
- **Access threads**: "Show me the conversation thread from that message"
- **Create canvases**: "Create a canvas document with our meeting notes"

## Documentation & Resources

- [Official Slack MCP Server Documentation](https://docs.slack.dev/ai/mcp-server/)

## Notes & Limitations

- **Remote server only**: This configuration connects to Slack's hosted MCP server. No local installation is required or supported.
- **Admin approval required**: Your Slack workspace administrator must approve MCP integration before you can use this feature.
- **Authentication**: The CLIENT_ID in the configuration is used for OAuth authentication with your Slack workspace.

## Questions or Issues?

For questions about the Slack MCP server or integration issues, please refer to the [official Slack documentation](https://docs.slack.dev/ai/mcp-server/) or contact your workspace administrator.

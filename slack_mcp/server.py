import json
import logging
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent
from connection import SlackConnection

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('slack_server')


class SlackServer(Server):
    """MCP server that handles Slack operations."""

    def __init__(self) -> None:
        super().__init__(name="slack-server")
        self.db = SlackConnection()
        logger.info("SlackServer initialized")

        @self.list_tools()
        async def get_supported_operations():
            return [
                Tool(
                    name="read_channel",
                    description=(
                        "Read recent messages from a Slack channel. "
                        "Provide the channel name (without #) and optionally the number of messages to fetch (default 10)."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "channel": {
                                "type": "string",
                                "description": "Channel name without #, e.g. 'general' or 'arr-analytics'"
                            },
                            "count": {
                                "type": "integer",
                                "description": "Number of messages to fetch (default 10)",
                                "default": 10
                            }
                        },
                        "required": ["channel"]
                    }
                ),
                Tool(
                    name="read_thread",
                    description=(
                        "Read all replies in a Slack thread. "
                        "Requires the channel name and the timestamp (ts) of the parent message. "
                        "Get the ts by calling read_channel with the channel first."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "channel": {
                                "type": "string",
                                "description": "Channel name without #, e.g. 'general'"
                            },
                            "thread_ts": {
                                "type": "string",
                                "description": "Timestamp of the parent message, e.g. '1771341599.829259'"
                            },
                            "count": {
                                "type": "integer",
                                "description": "Max number of replies to fetch (default 50)",
                                "default": 50
                            }
                        },
                        "required": ["channel", "thread_ts"]
                    }
                ),
                Tool(
                    name="search_messages",
                    description=(
                        "Search Slack messages across all channels. "
                        "Supports Slack search modifiers like 'in:#channel', 'from:@user', 'before:YYYY-MM-DD', 'after:YYYY-MM-DD'."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query, e.g. 'budget in:#finance' or 'from:@john deployment'"
                            },
                            "count": {
                                "type": "integer",
                                "description": "Number of results to return (default 20)",
                                "default": 20
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="send_message",
                    description=(
                        "Post a message to a Slack channel, or reply in a thread if thread_ts is provided. "
                        "Supports Slack mrkdwn formatting: *bold*, _italic_, `code`, ```code block```, "
                        "<https://url|link text>, :emoji:, > blockquote."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "channel": {
                                "type": "string",
                                "description": "Channel name without #, e.g. 'general'"
                            },
                            "text": {
                                "type": "string",
                                "description": "Message text (supports Slack mrkdwn formatting)"
                            },
                            "thread_ts": {
                                "type": "string",
                                "description": "Timestamp of the parent message to reply in a thread (optional)"
                            }
                        },
                        "required": ["channel", "text"]
                    }
                ),
                Tool(
                    name="send_direct_message",
                    description=(
                        "Send a direct message (DM) to a Slack user. "
                        "Accepts a username (e.g. 'john.doe'), display name, or user ID (e.g. 'U01ABC123'). "
                        "Supports Slack mrkdwn formatting."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user": {
                                "type": "string",
                                "description": "Username, display name, or user ID (with or without @)"
                            },
                            "text": {
                                "type": "string",
                                "description": "Message text (supports Slack mrkdwn formatting)"
                            }
                        },
                        "required": ["user", "text"]
                    }
                ),
            ]

        @self.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            logger.info(f"Tool called: {name} with args: {arguments}")
            try:
                if name == "read_channel":
                    result = self.db.read_channel(
                        arguments.get("channel", ""),
                        arguments.get("count", 10),
                    )
                elif name == "read_thread":
                    result = self.db.read_thread(
                        arguments.get("channel", ""),
                        arguments.get("thread_ts", ""),
                        arguments.get("count", 50),
                    )
                elif name == "search_messages":
                    result = self.db.search_messages(
                        arguments.get("query", ""),
                        arguments.get("count", 20),
                    )
                elif name == "send_message":
                    result = self.db.send_message(
                        arguments.get("channel", ""),
                        arguments.get("text", ""),
                        arguments.get("thread_ts"),
                    )
                elif name == "send_direct_message":
                    result = self.db.send_direct_message(
                        arguments.get("user", ""),
                        arguments.get("text", ""),
                    )
                else:
                    result = {"error": f"Unknown tool: {name}"}

                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            except Exception as e:
                error_msg = f"Error executing {name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return [TextContent(type="text", text=json.dumps({"error": error_msg}))]

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.cleanup()

import json
import logging
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent, Resource, ReadResourceResult, TextResourceContents
from connection import SlackConnection

SKILL_MD_PATH = Path(__file__).parent / "resources" / "SKILL.md"

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
                # --- FUTURE SCOPE: get_pending_questions ---
                # Enables an AI Q&A workflow where Claude polls a channel for
                # messages starting with a trigger prefix (e.g. "ask:") and
                # auto-replies in-thread. Requires an LLM API (Anthropic/Ollama)
                # to run as an automated bot. Re-enable when that is available.
                # See: slack_mcp/tools/GetPendingQuestions.py
                # ---------------------------------------------------

                Tool(
                    name="delete_message",
                    description=(
                        "Delete a Slack message by its timestamp (ts). "
                        "Works for both channel messages and direct messages. "
                        "Provide either 'channel' (for channel messages) or 'user' (for DMs), plus the 'ts' of the message. "
                        "You can only delete messages sent by yourself."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ts": {
                                "type": "string",
                                "description": "Timestamp of the message to delete, e.g. '1771341599.829259'"
                            },
                            "channel": {
                                "type": "string",
                                "description": "Channel name without # (for channel messages)"
                            },
                            "user": {
                                "type": "string",
                                "description": "Username or user ID (for DMs)"
                            }
                        },
                        "required": ["ts"]
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
                # FUTURE SCOPE: get_pending_questions (see list_tools comment)
                elif name == "delete_message":
                    result = self.db.delete_message(
                        arguments.get("ts", ""),
                        channel=arguments.get("channel"),
                        user=arguments.get("user"),
                    )
                else:
                    result = {"error": f"Unknown tool: {name}"}

                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            except Exception as e:
                error_msg = f"Error executing {name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return [TextContent(type="text", text=json.dumps({"error": error_msg}))]

        @self.list_resources()
        async def list_resources() -> list[Resource]:
            return [
                Resource(
                    uri="slack://skill",
                    name="Slack MCP Usage Guide",
                    description=(
                        "Usage guide and reference for all Slack MCP tools — "
                        "covers routing logic, auth, channel resolution, formatting, and troubleshooting."
                    ),
                    mimeType="text/markdown",
                )
            ]

        @self.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            if uri == "slack://skill":
                content = SKILL_MD_PATH.read_text(encoding="utf-8")
                return ReadResourceResult(
                    contents=[
                        TextResourceContents(
                            uri=uri,
                            mimeType="text/markdown",
                            text=content,
                        )
                    ]
                )
            raise ValueError(f"Unknown resource: {uri}")

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.cleanup()

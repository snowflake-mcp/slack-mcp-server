import logging
from typing import Any

logger = logging.getLogger('slack_tools')


class ReadChannel:
    """Mixin that provides Slack channel reading capabilities."""

    def read_channel(self, channel: str, count: int = 10) -> dict[str, Any]:
        """Read recent messages from a Slack channel."""
        channel_id = self.resolve_channel(channel)

        data = self.slack_request("conversations.history", {
            "channel": channel_id,
            "limit": count,
        })

        messages = []
        for msg in data.get("messages", []):
            user_id = msg.get("user") or msg.get("bot_id", "unknown")
            messages.append({
                "user": self.resolve_user(user_id),
                "text": msg.get("text", ""),
                "ts": msg.get("ts", ""),
                "reply_count": msg.get("reply_count", 0),
                "reactions": [
                    {"name": r["name"], "count": r["count"]}
                    for r in msg.get("reactions", [])
                ],
            })

        return {
            "channel": channel,
            "channel_id": channel_id,
            "message_count": len(messages),
            "messages": messages,
        }

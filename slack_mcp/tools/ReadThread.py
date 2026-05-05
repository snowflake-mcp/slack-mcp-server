import logging
from typing import Any

logger = logging.getLogger('slack_tools')


class ReadThread:
    """Mixin that provides Slack thread reading capabilities."""

    def read_thread(self, channel: str, thread_ts: str, count: int = 50) -> dict[str, Any]:
        """Read all replies in a Slack thread."""
        channel_id = self.resolve_channel(channel)

        data = self.slack_request("conversations.replies", {
            "channel": channel_id,
            "ts": thread_ts,
            "limit": count,
        })

        messages = []
        for msg in data.get("messages", []):
            user_id = msg.get("user") or msg.get("bot_id", "unknown")
            messages.append({
                "user": self.resolve_user(user_id),
                "text": msg.get("text", ""),
                "ts": msg.get("ts", ""),
                "is_parent": msg.get("ts") == thread_ts,
                "reactions": [
                    {"name": r["name"], "count": r["count"]}
                    for r in msg.get("reactions", [])
                ],
            })

        return {
            "channel": channel,
            "channel_id": channel_id,
            "thread_ts": thread_ts,
            "reply_count": len(messages) - 1,
            "messages": messages,
        }

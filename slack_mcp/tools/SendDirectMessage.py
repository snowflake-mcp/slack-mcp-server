import logging
from typing import Any

logger = logging.getLogger('slack_tools')


class SendDirectMessage:
    """Mixin that provides Slack direct messaging capabilities."""

    def send_direct_message(self, user: str, text: str) -> dict[str, Any]:
        """Send a direct message to a Slack user."""
        user_id = self.resolve_user_id(user)

        # Open (or reuse) the DM conversation
        dm = self.slack_request_post("conversations.open", {"users": user_id})
        dm_channel_id = dm.get("channel", {}).get("id", "")
        if not dm_channel_id:
            raise RuntimeError("Failed to open DM conversation.")

        data = self.slack_request_post("chat.postMessage", {
            "channel": dm_channel_id,
            "text": text,
        })

        return {
            "ok": True,
            "to_user": self.resolve_user(user_id),
            "user_id": user_id,
            "dm_channel_id": dm_channel_id,
            "ts": data.get("ts", ""),
        }

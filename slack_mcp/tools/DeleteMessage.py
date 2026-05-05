import logging
from typing import Any

logger = logging.getLogger('slack_tools')


class DeleteMessage:
    """Mixin that provides Slack message deletion for channels and DMs."""

    def delete_message(self, ts: str, channel: str = None, user: str = None) -> dict[str, Any]:
        """
        Delete a message by its timestamp.
        Provide either 'channel' (for channel messages) or 'user' (for DMs).
        """
        if not channel and not user:
            raise ValueError("Either 'channel' or 'user' must be provided.")

        if user:
            user_id = self.resolve_user_id(user)
            dm = self.slack_request_post("conversations.open", {"users": user_id})
            channel_id = dm.get("channel", {}).get("id", "")
            if not channel_id:
                raise RuntimeError("Failed to open DM conversation.")
        else:
            channel_id = self.resolve_channel(channel)

        self.slack_request_post("chat.delete", {"channel": channel_id, "ts": ts})

        return {
            "ok": True,
            "deleted_ts": ts,
            "channel_id": channel_id,
        }

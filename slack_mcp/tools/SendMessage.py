import logging
from typing import Any

logger = logging.getLogger('slack_tools')


class SendMessage:
    """Mixin that provides Slack message sending capabilities."""

    def send_message(self, channel: str, text: str, thread_ts: str = None) -> dict[str, Any]:
        """Post a message to a Slack channel, or reply in a thread if thread_ts is given."""
        channel_id = self.resolve_channel(channel)

        payload = {
            "channel": channel_id,
            "text": text,
        }
        if thread_ts:
            payload["thread_ts"] = thread_ts

        data = self.slack_request_post("chat.postMessage", payload)

        return {
            "ok": True,
            "channel": channel,
            "channel_id": channel_id,
            "ts": data.get("ts", ""),
            "thread_ts": thread_ts,
        }

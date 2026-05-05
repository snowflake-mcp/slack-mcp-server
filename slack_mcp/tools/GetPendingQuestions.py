import logging
from typing import Any

logger = logging.getLogger('slack_tools')


class GetPendingQuestions:
    """Mixin that fetches unanswered trigger messages from a Slack channel."""

    def get_pending_questions(
        self,
        channel: str,
        trigger: str = "ask:",
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Return messages that start with the trigger prefix and have no replies yet.
        Use send_message with the returned ts to post an answer in the thread.
        """
        channel_id = self.resolve_channel(channel)

        data = self.slack_request("conversations.history", {
            "channel": channel_id,
            "limit": limit,
        })

        pending = []
        for msg in data.get("messages", []):
            text = msg.get("text", "")
            if not text.lower().startswith(trigger.lower()):
                continue
            if msg.get("reply_count", 0) > 0:
                continue

            user_id = msg.get("user") or msg.get("bot_id", "unknown")
            pending.append({
                "ts": msg.get("ts", ""),
                "user": self.resolve_user(user_id),
                "question": text[len(trigger):].strip(),
                "raw_text": text,
            })

        return {
            "channel": channel,
            "channel_id": channel_id,
            "trigger": trigger,
            "pending_count": len(pending),
            "pending": pending,
            "instructions": (
                f"For each item above, call send_message with channel='{channel}', "
                "thread_ts=<ts>, and text=<your answer> to reply in the thread."
            ),
        }

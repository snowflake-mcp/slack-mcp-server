import logging
from typing import Any

logger = logging.getLogger('slack_tools')


class SearchMessages:
    """Mixin that provides Slack message search capabilities."""

    def search_messages(self, query: str, count: int = 20) -> dict[str, Any]:
        """Search Slack messages across all channels."""
        data = self.slack_request("search.messages", {
            "query": query,
            "count": count,
            "sort": "timestamp",
            "sort_dir": "desc",
        })

        matches = data.get("messages", {}).get("matches", [])
        results = []
        for msg in matches:
            user_id = msg.get("user") or msg.get("bot_id", "unknown")
            results.append({
                "channel": msg.get("channel", {}).get("name", "unknown"),
                "channel_id": msg.get("channel", {}).get("id", ""),
                "user": self.resolve_user(user_id),
                "text": msg.get("text", ""),
                "ts": msg.get("ts", ""),
                "permalink": msg.get("permalink", ""),
            })

        return {
            "query": query,
            "total": data.get("messages", {}).get("total", 0),
            "returned": len(results),
            "results": results,
        }

import os
import logging
import truststore
import requests
from dotenv import load_dotenv, find_dotenv
from tools.ReadChannel import ReadChannel
from tools.ReadThread import ReadThread
from tools.SearchMessages import SearchMessages
from tools.SendMessage import SendMessage
from tools.SendDirectMessage import SendDirectMessage
from tools.DeleteMessage import DeleteMessage

truststore.inject_into_ssl()

logger = logging.getLogger('slack_connection')

load_dotenv(find_dotenv())


class SlackConnection(ReadChannel, ReadThread, SearchMessages, SendMessage, SendDirectMessage, DeleteMessage):
    """Manages Slack API access using a user session token + cookie."""

    BASE_URL = "https://slack.com/api"

    def __init__(self) -> None:
        self.token = os.getenv("SLACK_TOKEN", "")
        self.cookie = os.getenv("SLACK_COOKIE", "")
        self._channel_cache: dict[str, str] = {}
        self._user_cache: dict[str, str] = {}

        if not self.token:
            raise ValueError("SLACK_TOKEN not set in .env")

        logger.info("SlackConnection initialized")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Cookie": f"d={self.cookie}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def slack_request(self, method: str, params: dict = None) -> dict:
        """Call a Slack Web API method via GET."""
        url = f"{self.BASE_URL}/{method}"
        response = requests.get(url, headers=self._headers(), params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack API error [{method}]: {data.get('error', 'unknown')}")
        return data

    def slack_request_post(self, method: str, payload: dict) -> dict:
        """Call a Slack Web API method via POST."""
        url = f"{self.BASE_URL}/{method}"
        response = requests.post(url, headers=self._headers(), json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack API error [{method}]: {data.get('error', 'unknown')}")
        return data

    def resolve_channel(self, channel: str) -> str:
        """Resolve a channel name to its ID, with in-memory caching."""
        name = channel.lstrip("#")

        if name.startswith(("C", "G", "D")) and len(name) > 8:
            return name

        if name in self._channel_cache:
            return self._channel_cache[name]

        data = self.slack_request("search.messages", {"query": f"in:#{name}", "count": 1})
        matches = data.get("messages", {}).get("matches", [])
        if not matches:
            raise ValueError(f"Channel '#{name}' not found or you are not a member.")

        ch = matches[0]["channel"]
        if ch["name"] != name:
            raise ValueError(f"Channel '#{name}' not found (got '#{ch['name']}' instead).")

        self._channel_cache[name] = ch["id"]
        logger.info(f"Resolved #{name} → {ch['id']}")
        return ch["id"]

    def resolve_user_id(self, user: str) -> str:
        """Resolve a username, display name, or email to a Slack user ID."""
        name = user.lstrip("@")

        # Already a user ID
        if name.startswith("U") and len(name) > 5:
            return name

        # Try users.list (may be paginated but works for most workspaces)
        try:
            cursor = None
            while True:
                params = {"limit": 200}
                if cursor:
                    params["cursor"] = cursor
                data = self.slack_request("users.list", params)
                for member in data.get("members", []):
                    profile = member.get("profile", {})
                    candidates = [
                        member.get("name", ""),
                        profile.get("display_name", ""),
                        profile.get("real_name", ""),
                        profile.get("email", "").split("@")[0],
                    ]
                    if name.lower() in [c.lower() for c in candidates if c]:
                        return member["id"]
                cursor = data.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
        except Exception:
            pass

        # Fall back: extract user ID from a search for messages from that user
        try:
            data = self.slack_request("search.messages", {"query": f"from:@{name}", "count": 1})
            matches = data.get("messages", {}).get("matches", [])
            if matches:
                uid = matches[0].get("user")
                if uid:
                    return uid
        except Exception:
            pass

        raise ValueError(f"User '{user}' not found. Try passing the user ID (e.g. U01ABC123) directly.")

    def resolve_user(self, user_id: str) -> str:
        """Resolve a user/bot ID to a display name, with in-memory caching."""
        if not user_id or user_id == "unknown":
            return user_id

        if user_id in self._user_cache:
            return self._user_cache[user_id]

        try:
            if user_id.startswith("B"):
                data = self.slack_request("bots.info", {"bot": user_id})
                name = data.get("bot", {}).get("name", user_id)
            else:
                data = self.slack_request("users.info", {"user": user_id})
                profile = data.get("user", {}).get("profile", {})
                name = profile.get("display_name") or profile.get("real_name") or user_id
        except Exception:
            name = user_id

        self._user_cache[user_id] = name
        return name

    def cleanup(self) -> None:
        pass

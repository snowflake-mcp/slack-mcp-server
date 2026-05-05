# Slack MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that lets AI assistants read and send Slack messages on your enterprise Slack workspace.

Connects using your personal Slack session token — no admin approval or bot registration required.

---

## Tools

| Tool | Description |
|---|---|
| `read_channel` | Read recent messages from a channel |
| `read_thread` | Read all replies in a thread |
| `search_messages` | Search messages across all channels |
| `send_message` | Post to a channel or reply in a thread |
| `send_direct_message` | Send a DM to any user by name or ID |
| `delete_message` | Delete a message from a channel or DM |

---

## Setup

### 1. Clone / navigate to the project

```bash
cd /path/to/slack-mcp-server
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

### 3. Get your Slack credentials

You need two values from your active Slack web session: a **token** and a **cookie**.

#### Step 1 — Open Slack in Chrome

Go to your enterprise Slack URL (e.g. `https://your-company.enterprise.slack.com`) and sign in. Click into any workspace.

#### Step 2 — Open DevTools

Press `Cmd + Option + I` (Mac) or right-click → **Inspect**.

#### Step 3 — Get the token

1. In DevTools, go to the **Application** tab
2. In the left sidebar, expand **Local Storage** → click `https://app.slack.com`
3. In the filter box, type `localConfig_v2`
4. Click the row to expand the value, then navigate to **teams → your workspace → `enterprise_api_token`**
5. Copy the value (starts with `xoxc-`)

#### Step 4 — Get the cookie

Go to **Application** tab → **Cookies** → `https://app.slack.com`.
Find the cookie named **`d`** and copy its value (starts with `xoxd-`).

### 4. Create the `.env` file

```bash
cp .env.example .env   # or create it manually
```

Edit `.env`:

```env
SLACK_TOKEN=xoxc-your-token-here
SLACK_COOKIE=xoxd-your-cookie-here
```

> **Note:** These credentials expire when your Slack session expires (typically weeks). Repeat Step 3–4 to refresh them.

### 5. Test the connection

```bash
venv/bin/python -c "
import sys; sys.path.insert(0, 'slack_mcp')
from connection import SlackConnection
c = SlackConnection()
data = c.slack_request('auth.test')
print('Connected as:', data.get('user'), '| Workspace:', data.get('team'))
"
```

---

## Register with Claude Code

Add the following to `~/.claude.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "slack": {
      "type": "stdio",
      "command": "/path/to/slack-mcp-server/venv/bin/python",
      "args": ["/path/to/slack-mcp-server/slack_mcp/main.py"],
      "env": {}
    }
  }
}
```

Then restart Claude Code or run `/mcp` to reload servers.

---

## Tool Reference

### `read_channel`

Read recent messages from a Slack channel.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `channel` | string | yes | — | Channel name without `#`, e.g. `general` |
| `count` | integer | no | 10 | Number of messages to fetch |

**Example:** *"Read the last 20 messages from #arr-analytics"*

---

### `read_thread`

Read all replies in a thread. Use `read_channel` first to get the `ts` of the parent message.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `channel` | string | yes | — | Channel name without `#` |
| `thread_ts` | string | yes | — | Timestamp of the parent message, e.g. `1771341599.829259` |
| `count` | integer | no | 50 | Max replies to fetch |

**Example:** *"Read the thread on the last message in #general"*

---

### `search_messages`

Search messages across all channels. Supports Slack search modifiers.

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `query` | string | yes | — | Search query |
| `count` | integer | no | 20 | Number of results |

**Supported modifiers:**

| Modifier | Example |
|---|---|
| Filter by channel | `in:#finance` |
| Filter by user | `from:@john.doe` |
| Date range | `after:2024-01-01 before:2024-06-01` |
| Combine | `deployment failed in:#on-call after:2024-01-01` |

**Example:** *"Search for messages about 'budget approval' in #finance"*

---

### `send_message`

Post a message to a channel. Pass `thread_ts` to reply in a thread instead.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `channel` | string | yes | Channel name without `#` |
| `text` | string | yes | Message text (supports mrkdwn) |
| `thread_ts` | string | no | Parent message `ts` to reply in a thread |

**Example:** *"Send 'Deployment complete' to #releases"*

---

### `send_direct_message`

Send a DM to any Slack user.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `user` | string | yes | Username, display name, or user ID (e.g. `U01ABC123`) |
| `text` | string | yes | Message text (supports mrkdwn) |

**Example:** *"DM john.doe with 'Can you review this PR?'"*

---

## Slack Message Formatting (mrkdwn)

| Syntax | Result |
|---|---|
| `*bold*` | **bold** |
| `_italic_` | *italic* |
| `` `code` `` | `code` |
| ` ```code block``` ` | code block |
| `<https://url\|link text>` | hyperlink |
| `<@USER_ID>` | user mention |
| `:emoji_name:` | emoji |
| `> text` | blockquote |

---

## Project Structure

```
slack-mcp-server/
├── slack_mcp/
│   ├── main.py              # Entrypoint — starts the MCP server
│   ├── server.py            # Tool definitions and request routing
│   ├── connection.py        # SlackConnection — API calls, channel/user resolution
│   └── tools/
│       ├── ReadChannel.py
│       ├── ReadThread.py
│       ├── SearchMessages.py
│       ├── SendMessage.py
│       └── SendDirectMessage.py
├── requirements.txt
├── .env                     # Your credentials (gitignored)
└── README.md
```

---

## Troubleshooting

**SSL certificate error**
The server uses `truststore` to pull corporate CA certs from the macOS Keychain automatically. If you still see SSL errors, make sure the Slack desktop app is open and your session is active.

**`enterprise_is_restricted` error**
This is expected — `conversations.list` is blocked on enterprise grids. The server uses `search.messages` for channel resolution instead, which works without elevated permissions.

**Token expired / auth fails**
Slack session tokens expire. Repeat Steps 3–4 in the Setup section to get fresh values and update `.env`.

**User not found in `send_direct_message`**
Try passing the user's Slack user ID directly (e.g. `U01ABC123`). You can find it by right-clicking a user's name in Slack → **Copy member ID**.

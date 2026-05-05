---
name: slack-enterprise
description: >-
  Read, post, and search Slack messages across the Workday enterprise workspace
  (workday.enterprise.slack.com) using slk-read, slk CLI, and slackApi. Use
  when the user asks to read a Slack channel, post messages or thread replies,
  search Slack messages, check unreads, read threads, or access any channel on
  the enterprise Slack workspace. Also use when the first-party Slack MCP
  (user-slack) returns channel_not_found.
---

# Slack Enterprise Access

## Two access methods

| Property | First-party MCP (user-slack) | slk-read / slk CLI |
|---|---|---|
| Workspace | `workday.slack.com` | `workday.enterprise.slack.com` (all Grid workspaces) |
| Private channels | Only if MCP authorized | Any channel the user belongs to |
| Rate limits | Managed by Slack | Managed locally via channel cache |

### Routing

1. Try the first-party MCP (`user-slack`) first
2. If `channel_not_found`, use `slk-read`
3. For channels explicitly on the enterprise workspace, use `slk-read` directly

## slk-read (preferred for reads)

Wraps `slk` with a local channel name→ID cache (1,000+ channels) to avoid
`conversations.list` rate limits. Always use `slk-read` instead of `slk read`.

```bash
# Read messages
slk-read <channel-name> [count] [--ts] [--threads] [--from DATE] [--to DATE]
slk-read arr-analytics 10
slk-read arr_analytics_super_user_group 5 --ts

# Read a thread (get ts from --ts flag above)
slk-read thread <channel> <ts> [count]

# Search messages (uses Slack search API directly)
slk-read search "query" [count]

# Cache management
slk-read cache-search <query>     # Find channels by name
slk-read cache-list               # Show all cached channels
slk-read cache-add <name> <ID>    # Manually add a channel
slk-read cache-refresh            # Rebuild cache (slow, use sparingly)
```

## slk (for other operations)

Use `slk` directly for non-read operations or when slk-read doesn't cover it:

```bash
slk auth                          # Verify auth
slk unread                        # Check unreads
slk send <channel-id> "message"   # Send a message (use ID from cache)
slk pins <channel-id>             # Pinned messages
slk dms                           # List DM conversations
slk read @username 50             # Read DMs
slk read <channel-id> 30 --ts --threads  # Read with expanded threads
```

## Posting messages and thread replies

`slk send` posts to a channel but does **not** support thread replies. For
thread replies, use the `slackApi` function from the slkcli module:

```javascript
node -e "
const { slackApi } = require('/usr/local/lib/node_modules/slkcli/src/api.js');
slackApi('chat.postMessage', {
  channel: '<CHANNEL_ID>',
  thread_ts: '<PARENT_TS>',
  text: 'Thread reply text with *bold* and <https://url|link text>',
  unfurl_links: false
}).then(r => console.log(JSON.stringify(r)))
  .catch(e => console.error(e));
"
```

The `slackApi` function handles auth automatically (same Keychain session as
`slk`). It works for any Slack Web API method: `chat.postMessage`,
`chat.delete`, `chat.update`, `reactions.add`, etc.

### Slack message formatting (mrkdwn)

- `*bold*`, `_italic_`, `~strikethrough~`, `` `code` ``
- ` ```code block``` `
- `<https://url|display text>` for links
- `<@USER_ID>` for mentions
- `:emoji_name:` for emoji
- `> quoted text` for blockquotes

## Shell requirements

- Always use `required_permissions: ["all"]` (Keychain access)
- Set `block_until_ms: 30000` minimum (API calls take 5-25s)
- For threads, set `block_until_ms: 15000`

## Workflow: read latest message with replies

```bash
# Step 1: Read with timestamps
slk-read <channel> 5 --ts

# Step 2: Read thread using ts value
slk-read thread <channel> <ts_value>
```

## Workflow: find a channel

```bash
# Search the local cache first (instant, no API call)
slk-read cache-search "arr"

# If not found, ask user for channel ID or run cache-refresh
```

## Troubleshooting

- **`slk-read` fails with `env: node\r: No such file or directory`**: Windows
  line-ending issue in the script. Use `slk read <channel-id> <count>` directly
  as a fallback (requires channel ID, not name).
- **Auth fails**: open the Slack desktop app so the Keychain session refreshes.
- **`slk send <channel> --help` sends "--help" as a message**: `slk send` has
  no `--help` flag — the second positional arg is always the message body.

## Notes

- Auth is automatic from the Slack desktop app session (Keychain)
- If auth fails, ask user to open the Slack desktop app
- Token auto-refreshes; cache is valid for 7 days
- The user acts as themselves (session identity, not a bot)
- `slk auth` shows the workspace URL — verify it matches the target workspace

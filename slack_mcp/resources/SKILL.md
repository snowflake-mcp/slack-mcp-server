---
name: slack-enterprise
description: >-
  Read, post, and search Slack messages across the enterprise workspace
  using the Slack MCP server tools. Use when the user asks to read a Slack
  channel, post messages or thread replies, search Slack messages, check
  unreads, read threads, or send direct messages.
---

# Slack Enterprise Access

## Available Tools

| Tool | Description |
|---|---|
| `read_channel` | Read recent messages from a channel |
| `read_thread` | Read all replies in a thread (needs `ts` from read_channel) |
| `search_messages` | Search messages across all channels |
| `send_message` | Post to a channel or reply in a thread |
| `send_direct_message` | Send a DM to a user by name or ID |
| `delete_message` | Delete a message from a channel or DM |

## Routing

1. Use `read_channel` to get messages — always returns resolved usernames
2. Use `read_thread` to expand a threaded conversation — get `ts` from `read_channel` output
3. Use `search_messages` for cross-channel search — supports Slack modifiers
4. Before replying in a thread, always show the user the message you plan to send and ask for confirmation — then use `send_message` with `thread_ts` to post the reply
5. Use `send_direct_message` for user-to-user messages

## read_channel

```
read_channel(channel, count=10)
```

- `channel`: name without `#`, e.g. `general` or `arr-analytics`
- `count`: number of messages (default 10, max 100)

## read_thread

```
read_thread(channel, thread_ts, count=50)
```

- Get `thread_ts` from the `ts` field in `read_channel` output
- Returns all replies including the parent message

## search_messages

```
search_messages(query, count=20)
```

**Supported modifiers:**

| Modifier | Example |
|---|---|
| Filter by channel | `in:#finance` |
| Filter by user | `from:@john.doe` |
| Date range | `after:2024-01-01 before:2024-06-01` |
| Combine | `deployment failed in:#on-call after:2024-01-01` |

## send_message

```
send_message(channel, text, thread_ts=None)
```

- Omit `thread_ts` to post to channel
- Include `thread_ts` to reply in a thread

## send_direct_message

```
send_direct_message(user, text)
```

- `user`: username, display name, or user ID (`U01ABC123`)
- Accepts with or without `@`

## delete_message

```
delete_message(ts, channel=None, user=None)
```

- Provide `channel` for channel messages
- Provide `user` for DM messages
- Can only delete your own messages

## Slack Message Formatting (mrkdwn)

- `*bold*`, `_italic_`, `~strikethrough~`, `` `code` ``
- ` ```code block``` `
- `<https://url|display text>` for links
- `<@USER_ID>` for mentions
- `:emoji_name:` for emoji
- `> quoted text` for blockquotes

## Troubleshooting

- **Channel not found**: ensure you are a member of the channel
- **SSL errors**: handled automatically via truststore (macOS Keychain)
- **enterprise_is_restricted**: expected — channel resolution uses search.messages instead
- **Token expired**: refresh `SLACK_TOKEN` and `SLACK_COOKIE` in `.env` from browser DevTools
- **User not found**: pass the user ID directly (right-click user in Slack → Copy member ID)

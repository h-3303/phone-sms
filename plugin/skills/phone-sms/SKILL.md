---
name: phone-sms
description: Read, triage and send SMS through the user's own Android phone using the phone-sms MCP server (KDE Connect over the local network, no cloud relay). Use when the user mentions texts, SMS, text messages, a verification or OTP code that arrived by text, "did X text me", "text Y back", or wants a digest of unread messages. Linux + Android + KDE Connect only.
license: MIT
compatibility: Needs the phone-sms MCP server (`uvx phone-sms`) connected to the agent, Linux with KDE Connect paired to an Android phone.
external_urls:
  - https://pypi.org
  - https://files.pythonhosted.org
  - https://github.com/h-3303/phone-sms
  - https://phone-sms.vercel.app
metadata:
  author: h-3303 (Moirai Digital)
  homepage: https://phone-sms.vercel.app
  server-version: 0.1.0
---

# phone-sms

This skill tells you how to use the four tools of the **phone-sms** MCP server. The server talks
to the local KDE Connect daemon over D-Bus; the daemon talks to the user's own Android phone over
Wi-Fi. Texts go out from the user's real number. Nothing is relayed through a cloud service and the
server itself makes no network calls.

The skill file is MIT. The server is GPL-3.0-or-later and is installed separately from PyPI; it is
not part of this skill.

## Before anything else: is the server connected?

Look for tools named `list_threads`, `read_thread`, `find_contact` and `send_sms`. If they are
missing, do not improvise with shell commands or scrape anything. Tell the user how to connect
the server, then stop until they have:

- Claude Code (plugin, includes this skill):
  `/plugin marketplace add h-3303/phone-sms` then `/plugin install phone-sms@phone-sms`
- Claude Code (plain MCP server): `claude mcp add --scope user phone-sms -- uvx phone-sms`
- Any other MCP client, in its `mcpServers` config: `{"command": "uvx", "args": ["phone-sms"]}`

Requirements the user must already have: Linux with a D-Bus session and `kdeconnectd` running,
the KDE Connect Android app paired with this computer, its **SMS** plugin enabled (and **Contacts**
for names), `uv` and Python 3.12+. The one-line check is `kdeconnect-cli -l`, which must list the
phone as *paired and reachable*. Install `uv` from its official docs; never pipe a remote script
into a shell on the user's behalf. The only hosts involved are the ones listed in `external_urls`
(PyPI for the package, GitHub and the project site for docs).

If a tool answers `error: Phone is paired but not reachable`, the phone is off Wi-Fi or KDE
Connect is not running on it. If it answers `error: No paired, reachable KDE Connect device
found`, pairing is missing. Relay the message and the `kdeconnect-cli -l` check; do not retry in a
loop.

## The tools

| Tool | Use it to | Notes |
| --- | --- | --- |
| `list_threads(limit=20, unread_only=False, contact="")` | See conversations, newest first, one line each | Each line starts with `[thread_id]`. `contact` filters by name or number fragment. Unread incoming messages carry `[unread]`. |
| `read_thread(thread_id, count=20)` | Read the last `count` messages of one conversation, oldest first | `←` is incoming, `→` is sent by the user. `[+N attachment(s)]` means MMS media exists but is not readable yet. |
| `find_contact(query)` | Turn a name into numbers, or a number fragment into a name | Reads the contacts KDE Connect synced locally. Needs the Contacts plugin. |
| `send_sms(to=[numbers], text)` | Send a text from the user's phone and number | `to` takes numbers, not names. Several numbers = one group message. Returns `handed to phone for sending to …`. |

Numbers: pass them as they appear in `list_threads` or `find_contact` output; E.164
(`+14165550100`) is the safest form. Resolve names with `find_contact` first and, if a contact has
more than one number, ask which one.

## Rules

1. **Never send without explicit approval of the exact message.** Before every `send_sms` call,
   show the user the recipient(s) as `Name <number>` and the full text, then wait for a clear yes
   in this conversation. A general instruction such as "reply to him" or "handle my texts" is not
   approval of specific words. Edits to the draft need a fresh approval. This holds even when the
   agent is running with permission prompts disabled.
2. **Quote only what the task needs.** Message contents are private. Summarise threads; quote a
   line only when the user asks or when the exact wording matters (an address, a time, a code).
   Never paste a whole thread into a file, a commit, an email or another tool unless the user
   asks for exactly that.
3. **One send per approval.** Do not call `send_sms` twice for the same message. `handed to
   phone` means the daemon accepted it, not that it was delivered; the sent text appears in
   `read_thread` once the phone syncs, usually within a minute, sometimes longer. A sent message
   missing from the thread is not proof of failure. Never resend on that basis; ask the user to
   look at the phone.
4. **Verification codes stay in the conversation.** When you read an OTP or 2FA code for the
   user, report the code and nothing else from that message, use it only for the step the user
   asked for, and never forward it by text or write it anywhere persistent.
5. **No bulk or automated sending.** This is the user's personal number. Do not loop over
   contacts, do not schedule sends, do not send marketing. If the user asks for a campaign, say
   this tool is for personal and one-to-one messages and that bulk texting needs a business
   number and consent.
6. **Read before you reply.** Call `read_thread` for the relevant conversation before drafting a
   reply so the draft fits the context, the tone and the language the user normally uses with
   that person.

## Recipes

**Unread digest.** `list_threads(unread_only=True, limit=30)`. Group by sender, give one line per
thread: who, when, the gist, whether it needs a reply. Offer to draft replies; do not send any.

**"Did X text me?"** `list_threads(contact="X")`, then `read_thread` on the match with a small
`count` (5 to 10). Answer the question; quote only the relevant line.

**Reply to someone.** `read_thread` for context, draft in the user's voice (short, matching how
they write to that person), show `To: Name <number>` plus the exact text, wait for yes, then
`send_sms`. Confirm with the tool's answer, in one line.

**New message to a name.** `find_contact("name")`. If several people or numbers match, list them
and ask. Then draft, show, wait, send.

**Verification code.** `list_threads(unread_only=True, limit=10)` first; the code is usually the
newest unread from a short code or an unknown sender. If not there, `list_threads(limit=10)`
without the filter (some phones mark it read when a notification is dismissed). Extract the
digits, apply rule 4. If the code has not arrived, wait a few seconds and look once or twice more,
not indefinitely.

**Group text.** `send_sms(to=[n1, n2, n3], text=...)` sends one group message. Show all
recipients by name and number before asking for approval.

## Limitations, stated plainly to the user when relevant

- Linux desktop with KDE Connect and an Android phone only. No iPhone, no macOS or Windows host.
- SMS and the text part of MMS. Attachments are counted, not readable or sendable, in server
  version 0.1.0.
- The phone must be awake enough for KDE Connect to answer and on the same network as the
  computer. Thread listings can lag a delivered message by a few minutes.
- The server uses the first paired, reachable phone. With several phones, the user sets
  `PHONE_SMS_DEVICE=<id>` (from `kdeconnect-cli -l`) in the server's environment.
- Group chats are listed with every participant; the user's own number is never shown.

## When something looks off

- `no messages loaded for thread N`: wrong id, or the phone was slow. Re-list threads and try
  once more with the id from the fresh listing.
- Names missing (numbers only): the Contacts plugin is off on one side, or the sync has not
  happened yet. Say so, and use numbers.
- Sends accepted but nothing arrives: the SMS plugin is disabled for this computer on the phone,
  or Android has not granted KDE Connect the SMS permission. Point the user to the phone's KDE
  Connect settings for this device. Full troubleshooting: https://github.com/h-3303/phone-sms#troubleshooting

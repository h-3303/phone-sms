# phone-sms

**Site:** https://phone-sms.vercel.app · **Repo:** https://github.com/h-3303/phone-sms

<!-- mcp-name: io.github.h-3303/phone-sms -->

An MCP server that lets Claude (or any MCP client) read and send SMS through your own Android
phone, from your own number. It talks to the phone over **KDE Connect** on your local network:
no cloud relay, no SMS gateway account, no app to install beyond KDE Connect itself.

```
agent ──MCP──▶ phone-sms ──D-Bus──▶ kdeconnectd ──LAN──▶ KDE Connect (Android) ──▶ SMS
```

Tools:

| Tool | Does |
| --- | --- |
| `list_threads` | conversations, newest first, with the latest message; filter by contact or unread |
| `read_thread` | the last *n* messages of one conversation |
| `find_contact` | look up a contact by name or number fragment (from the phone's synced contacts) |
| `send_sms` | send a text, or a group text to several numbers |

`send_sms` carries MCP's `destructiveHint`, and the server tells the model never to send until you
have approved the exact recipient and text in the conversation. Message contents never leave your
machine except as the model's context.

## Requirements

- Linux with a D-Bus session bus and **KDE Connect** (`kdeconnectd`, a current release; package
  `kdeconnect`). It does not need the Plasma desktop; it runs fine under GNOME, Hyprland, Sway…
- An Android phone with the **KDE Connect** app ([F-Droid](https://f-droid.org/packages/org.kde.kdeconnect_tp/) /
  [Play](https://play.google.com/store/apps/details?id=org.kde.kdeconnect_tp)), paired with the computer.
  On the phone, enable the **SMS** plugin (and **Contacts** if you want names) and grant the SMS and
  contacts permissions it asks for.
- [uv](https://docs.astral.sh/uv/) and Python 3.12+.

Check the pairing: `kdeconnect-cli -l` should list your phone as *paired and reachable*.

## Install

**Claude Code, as a plugin** (one step):

```
/plugin marketplace add h-3303/phone-sms
/plugin install phone-sms@phone-sms
```

**Claude Code, as a plain MCP server:**

```bash
claude mcp add --scope user phone-sms -- uvx phone-sms
```

**Any other MCP client** (Claude Desktop config shape, Cursor, Zed, …):

```json
{
  "mcpServers": {
    "phone-sms": {
      "command": "uvx",
      "args": ["phone-sms"]
    }
  }
}
```

From a checkout: `uv run --directory /path/to/phone-sms -q phone-sms`.

The server uses the first paired, reachable device. With several phones, pin one with
`PHONE_SMS_DEVICE=<id>` (the id `kdeconnect-cli -l` prints).

## CLI

The same code paths, for checking things by hand:

    phone-sms threads [-n 20] [--unread]
    phone-sms read <thread_id> [-n 20]
    phone-sms contact <name>
    phone-sms send <number>... -m "text"
    phone-sms                              # MCP server on stdio

## How sending works

1. `find_contact <name>` gives the number; `send_sms` takes numbers, ideally in E.164 (`+14375551234`).
2. The model shows you recipient and text and waits for your yes.
3. `send_sms` answers *handed to phone…* once `kdeconnectd` has accepted the request. That is not
   delivery: the sent message shows up in `list_threads` / `read_thread` once the phone syncs it,
   usually within a minute.

## Troubleshooting

- **"no paired, reachable device"**: open KDE Connect on the phone, same Wi-Fi, `kdeconnect-cli -l`.
- **Sent, but nothing arrives**: on the phone, check that the SMS plugin is enabled for this computer
  and that Android granted KDE Connect the SMS permission. Watch the request leave the server with
  `dbus-monitor --session "interface='org.kde.kdeconnect.device.conversations',member='sendWithoutConversation'"`.
- **Names missing**: enable the Contacts plugin on both ends; vCards land in
  `~/.local/share/kpeoplevcard/kdeconnect-<device>/`.
- The `kdeconnectd` journal line *Unimplemented conversation of type 'r'* comes from the
  notification-forwarding plugin, not SMS.

## Notes for hackers

It uses `org.kde.kdeconnect.device.conversations`, the interface the `kdeconnect-sms` app uses.
The daemon object's introspection XML has duplicate methods, so device discovery is a raw D-Bus
call. `requestConversation` first emits only cached messages, so `read_thread` waits for `count`
messages or `conversationLoaded`, not for a quiet gap.

## License

GPL-3.0-or-later, like KDE Connect.

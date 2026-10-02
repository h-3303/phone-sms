# phone-sms

MCP server that lets Claude Code read and send SMS through the phone paired with
KDE Connect (Pixel 7 / GrapheneOS). Everything stays on the LAN: it talks to the local
`kdeconnectd` over D-Bus (`org.kde.kdeconnect.device.conversations`), the same interface
`kdeconnect-sms` uses. Contact names come from the vCards the contacts plugin syncs to
`~/.local/share/kpeoplevcard/kdeconnect-<device>/`.

Tools: `list_threads`, `read_thread`, `find_contact`, `send_sms`.

    uv run phone-sms threads [-n 20] [--unread]   # manual checks, same code paths
    uv run phone-sms read <thread_id> [-n 20]
    uv run phone-sms contact <name>
    uv run phone-sms send <number>... -m "text"
    uv run phone-sms                              # MCP server on stdio

Registered with `claude mcp add --scope user phone-sms -- uv run --directory ~/dev/phone-sms -q phone-sms`.
The device is the first paired+reachable one; pin it with `PHONE_SMS_DEVICE=<id>`.

Gotchas: the daemon object's introspection XML has duplicate methods, so `devices` is a raw
D-Bus call. `requestConversation` first emits only cached messages, so `read_thread` waits for
`count` messages or `conversationLoaded`, not for a quiet gap.

## Sending (verified 2026-10-02)

1. `find_contact <name>` → number; pass `to` in E.164 (`+14375551234`).
2. Get the user's explicit OK on recipient + exact text.
3. `send_sms` returns "handed to phone…" once the daemon accepts the D-Bus call. That is not
   delivery: confirm with `list_threads` / `read_thread` (the sent text appears after the phone syncs).
4. If it never appears: `kdeconnect-cli -l` must say "paired and reachable", and on the phone the
   KDE Connect SMS plugin plus Android's SMS permission must be on. Watch the call leave with
   `dbus-monitor --session "interface='org.kde.kdeconnect.device.conversations',member='sendWithoutConversation'"`.
   The journal line "Unimplemented conversation of type 'r'" comes from the sendnotifications plugin, not SMS.

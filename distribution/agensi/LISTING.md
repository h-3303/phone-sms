# Agensi listing: phone-sms

Everything to paste into the Creator Dashboard (agensi.io/dashboard/submit). Upload
`dist/agensi/phone-sms.zip` from `./distribution/agensi/build.sh`. Price: **Free**.
Keep this file in sync with `plugin/skills/phone-sms/SKILL.md`.

## Title
phone-sms: read and send your own texts from Claude, locally (Linux + Android)

## One-line description
Lets your agent read, triage and reply to SMS through your own Android phone over KDE Connect on your LAN. Your number, no cloud relay, no Twilio, no ADB. Sends only after you approve the exact text.

## Tags
sms, text-messages, android, kde-connect, linux, messaging, phone, otp, local-first, privacy, mcp, personal-assistant

## About this skill

**What it does**
Gives Claude Code (or any agent with MCP) four tools on your own phone: list conversations, read a thread, look up a contact, send a text. The skill teaches the agent when to reach for them, how to triage unread messages into a digest, how to find a verification code without echoing the rest of the message, and how to draft a reply in your voice and show it to you before anything is sent.

**How it works**
The phone-sms MCP server runs on your Linux machine and talks to the KDE Connect daemon over D-Bus, the same interface the KDE Connect SMS app uses. KDE Connect carries it to your paired Android phone over your Wi-Fi. Texts leave from your real number through your carrier. The server opens no network sockets of its own and has no account, key or telemetry. This skill is the instruction layer; the server is installed separately from PyPI with one command (`uvx phone-sms`), and the skill tells the agent exactly how to do that if the tools are missing.

**Frameworks and tools**
Works with any MCP client: Claude Code (as a plugin that bundles this skill, or as a plain MCP server), Claude Desktop, Cursor, Codex, Zed, Gemini CLI and others. Needs Linux with a D-Bus session, KDE Connect (`kdeconnectd`, no Plasma needed; fine under GNOME, Hyprland, Sway), the KDE Connect Android app paired with the SMS plugin on, `uv` and Python 3.12+.

**Why this beats prompting it yourself**
Without the skill the model has four bare tool names and will happily send on a vague "reply to him". The skill adds the rules that matter with a personal number: show recipient and exact text and wait for a yes, one send per approval, never resend because a thread looks stale, quote only what the task needs, keep OTP codes in the conversation, no bulk sends. It also encodes the operational knowledge: thread ids, E.164 numbers, name resolution, sync lag, what "handed to phone" means, and the `kdeconnect-cli -l` preflight that solves most setup problems.

## Known limitations
- Linux host + Android phone + KDE Connect only. No iPhone, macOS or Windows.
- SMS and the text of MMS; attachments are counted, not readable or sendable, in server 0.1.0.
- Phone must be on the same network with KDE Connect running; listings can lag a delivered message by minutes.
- Runs locally only. It cannot be executed on Agensi's servers ("run skill"); install it and the server on your own machine.

## Needs access to
- The KDE Connect SMS plugin on your phone (reads conversations, sends texts from your number).
- Optionally the KDE Connect Contacts plugin, for names instead of numbers (read from vCards already synced to `~/.local/share/kpeoplevcard/`).
- Network: PyPI (`pypi.org`, `files.pythonhosted.org`) once, to install the server with `uvx`. Nothing else.

## Documentation
- docs_url: https://phone-sms.vercel.app
- Repository and troubleshooting: https://github.com/h-3303/phone-sms
- Privacy: https://phone-sms.vercel.app/privacy
- Demo (GIF): https://phone-sms.vercel.app/demo.gif

## Licence (state in the listing body)
The skill file (SKILL.md) is MIT. The phone-sms server it drives is GPL-3.0-or-later, is not included in this download, and is installed from PyPI under its own licence. The MIT text ships inside the ZIP.

## FAQ
1. **Does my data go through Agensi or any cloud?** No. The skill is a text file. The server talks only to KDE Connect on your machine; the message travels from your phone over your carrier like any text you type.
2. **Will it send texts on its own?** No. The tool is marked destructive, the server's instructions and this skill both require the agent to show you the recipient and the exact wording and wait for your yes, and Claude Code adds its own permission prompt.
3. **Do I need a Twilio account or a second number?** No. It uses your own SIM and number through the KDE Connect app you may already have.
4. **Can I use it on macOS or Windows, or with an iPhone?** Not yet. It needs a Linux D-Bus session and the KDE Connect Android app. Those are the next things on the roadmap after MMS and OTP helpers.
5. **How do I set it up?** Pair KDE Connect with your phone and turn on its SMS plugin, check `kdeconnect-cli -l` shows the phone as paired and reachable, then `claude mcp add --scope user phone-sms -- uvx phone-sms` (or the Claude Code plugin: `/plugin marketplace add h-3303/phone-sms`). The skill repeats these steps to the agent if it finds the tools missing.

## Example session
> **you:** any unread texts? if the dentist wants a confirmation, draft one
> **agent:** *(list_threads unread_only, read_thread 412)* Two unread: a parcel notice, and Maple Dental asking you to confirm Tue 14 Oct, 2:30 pm. Draft: To Maple Dental <+15195550142>: "Confirmed for Tuesday Oct 14 at 2:30, thank you." Send it?
> **you:** yes
> **agent:** *(send_sms)* handed to phone for sending to Maple Dental <+15195550142>. Sent from your own number; no cloud relay.

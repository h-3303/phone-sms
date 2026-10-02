"""MCP server: read and send SMS through the phone paired with KDE Connect."""

import re

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from .contacts import Book
from .kdc import Message, Phone, PhoneError

mcp = MCPServer(
    "phone-sms",
    instructions=(
        "Reads and sends SMS through the user's own phone (KDE Connect, local network only). "
        "Message contents are private: quote only what the task needs. "
        "Never call send_sms until the user has explicitly approved the exact recipient and text in this conversation."
    ),
)
phone = Phone()
book = Book()


def _fmt(m: Message, who: bool = True) -> str:
    arrow = "→" if m.type == "out" else "←"
    peer = ", ".join(book.label(a) for a in m.addresses)
    unread = "" if m.read or m.type == "out" else " [unread]"
    att = f" [+{m.attachments} attachment(s)]" if m.attachments else ""
    head = f"{m.date:%Y-%m-%d %H:%M} {arrow}"
    if who:
        head += f" {peer}"
    return f"{head}{unread}: {m.body}{att}"


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_threads(limit: int = 20, unread_only: bool = False, contact: str = "") -> str:
    """List SMS conversations, newest first, with the latest message of each.

    Each line starts with the thread id, which read_thread takes.
    contact: optional name or number fragment to filter on.
    """
    try:
        msgs = await phone.threads()
    except PhoneError as e:
        return f"error: {e}"
    if unread_only:
        msgs = [m for m in msgs if not m.read and m.type != "out"]
    if contact:
        q = contact.lower()
        msgs = [m for m in msgs if any(q in book.label(a).lower() for a in m.addresses)]
    lines = [f"[{m.thread_id}] {_fmt(m)}" for m in msgs[:limit]]
    return "\n".join(lines) or "no matching threads"


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def read_thread(thread_id: int, count: int = 20) -> str:
    """Read the most recent `count` messages of one conversation, oldest first."""
    try:
        msgs = await phone.conversation(thread_id, count)
    except PhoneError as e:
        return f"error: {e}"
    if not msgs:
        return f"no messages loaded for thread {thread_id} (wrong id, or the phone did not answer in time)"
    peers = sorted({a for m in msgs for a in m.addresses})
    head = f"thread {thread_id} with " + ", ".join(book.label(p) for p in peers)
    return "\n".join([head, *(_fmt(m, who=len(peers) > 1) for m in msgs)])


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def find_contact(query: str) -> str:
    """Look up phone contacts by name or number fragment."""
    hits = book.search(query)
    return "\n".join(f"{n}: {', '.join(t)}" for n, t in hits) or "no contact matches"


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True, openWorldHint=True))
async def send_sms(to: list[str], text: str) -> str:
    """Send an SMS (several numbers = group message) from the user's phone and number.

    ONLY call after the user has explicitly approved this exact recipient list and text.
    `to` takes phone numbers; resolve names with find_contact first.
    """
    bad = [n for n in to if len(re.sub(r"\D", "", n)) < 3]
    if not to or bad:
        return f"error: invalid number(s): {bad or to}"
    if not text.strip():
        return "error: empty message"
    try:
        await phone.send(to, text)
    except PhoneError as e:
        return f"error: {e}"
    return f"handed to phone for sending to {', '.join(book.label(n) for n in to)}"


def serve() -> None:
    mcp.run("stdio")

"""phone-sms: CLI for manual checks; with no arguments, runs the MCP server on stdio."""

import argparse
import asyncio


def main() -> None:
    p = argparse.ArgumentParser(prog="phone-sms")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("serve", help="run the MCP server on stdio (default)")
    t = sub.add_parser("threads", help="list conversations")
    t.add_argument("-n", type=int, default=20)
    t.add_argument("--unread", action="store_true")
    r = sub.add_parser("read", help="read one conversation")
    r.add_argument("thread_id", type=int)
    r.add_argument("-n", type=int, default=20)
    c = sub.add_parser("contact", help="search contacts")
    c.add_argument("query")
    s = sub.add_parser("send", help="send an SMS")
    s.add_argument("number", nargs="+")
    s.add_argument("-m", "--message", required=True)
    a = p.parse_args()

    from . import server

    if a.cmd in (None, "serve"):
        server.serve()
    elif a.cmd == "threads":
        print(asyncio.run(server.list_threads(a.n, a.unread)))
    elif a.cmd == "read":
        print(asyncio.run(server.read_thread(a.thread_id, a.n)))
    elif a.cmd == "contact":
        print(server.find_contact(a.query))
    elif a.cmd == "send":
        print(asyncio.run(server.send_sms(a.number, a.message)))

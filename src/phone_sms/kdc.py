"""KDE Connect SMS over D-Bus (the same interface kdeconnect-sms uses)."""

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime

from dbus_next import BusType, MessageType, Variant
from dbus_next import Message as Message_
from dbus_next.aio import MessageBus

SERVICE = "org.kde.kdeconnect"
DAEMON_PATH = "/modules/kdeconnect"
CONV_IFACE = "org.kde.kdeconnect.device.conversations"

# Android Telephony.Sms MESSAGE_TYPE_*
TYPES = {1: "in", 2: "out", 3: "draft", 4: "outbox", 5: "failed", 6: "queued"}


@dataclass
class Message:
    body: str
    addresses: list[str]
    date: datetime
    type: str
    read: bool
    thread_id: int
    uid: int
    attachments: int

    @classmethod
    def from_variant(cls, v: Variant) -> "Message":
        # (isa(s)xiixixa(xsss)): event, body, addresses, date ms, type, read,
        # threadID, uID, subID, attachments
        _ev, body, addrs, date, typ, read, thread, uid, _sub, att = v.value
        return cls(
            body=body,
            addresses=[a[0] for a in addrs],
            date=datetime.fromtimestamp(date / 1000),
            type=TYPES.get(typ, str(typ)),
            read=bool(read),
            thread_id=thread,
            uid=uid,
            attachments=len(att),
        )


class PhoneError(RuntimeError):
    pass


class Phone:
    def __init__(self) -> None:
        self.bus: MessageBus | None = None
        self.device_id: str | None = None
        self._conv = None

    async def _connect(self):
        if self.bus is None or not self.bus.connected:
            self.bus = await MessageBus(bus_type=BusType.SESSION).connect()
            self._conv = None
        if self._conv is None:
            self.device_id = await self._pick_device()
            path = f"{DAEMON_PATH}/devices/{self.device_id}"
            intro = await self.bus.introspect(SERVICE, path)
            obj = self.bus.get_proxy_object(SERVICE, path, intro)
            self._conv = obj.get_interface(CONV_IFACE)
            self._device = obj.get_interface("org.kde.kdeconnect.device")
        if not await self._device.get_is_reachable():
            raise PhoneError("Phone is paired but not reachable. Is it on the same Wi-Fi with KDE Connect running?")
        return self._conv

    async def _pick_device(self) -> str:
        if env := os.environ.get("PHONE_SMS_DEVICE"):
            return env
        # raw call: the daemon's introspection XML has duplicate methods, which proxies reject
        reply = await self.bus.call(Message_(
            destination=SERVICE, path=DAEMON_PATH, interface="org.kde.kdeconnect.daemon",
            member="devices", signature="bb", body=[True, True],  # onlyReachable, onlyPaired
        ))
        if reply.message_type == MessageType.ERROR:
            raise PhoneError(f"KDE Connect daemon: {reply.body}")
        ids = reply.body[0]
        if not ids:
            raise PhoneError("No paired, reachable KDE Connect device found.")
        return ids[0]

    async def threads(self, refresh_wait: float = 2.0) -> list[Message]:
        """Latest message of every thread, newest first."""
        conv = await self._connect()
        await conv.call_request_all_conversation_threads()
        await asyncio.sleep(refresh_wait)  # phone pushes updated threads asynchronously
        msgs = [Message.from_variant(v) for v in await conv.call_active_conversations()]
        return sorted(msgs, key=lambda m: m.date, reverse=True)

    async def conversation(self, thread_id: int, count: int = 20, timeout: float = 10.0) -> list[Message]:
        """Most recent `count` messages of one thread, oldest first."""
        conv = await self._connect()
        got: dict[int, Message] = {}
        settled = asyncio.Event()
        loop = asyncio.get_running_loop()
        quiet: list[asyncio.TimerHandle] = []
        loaded = False

        def poke():
            # done once we have enough, or the phone said it finished and messages stopped arriving;
            # before that, the cache may hold only the thread's latest message
            if len(got) >= count:
                settled.set()
            elif loaded:
                for h in quiet:
                    h.cancel()
                quiet[:] = [loop.call_later(0.5, settled.set)]

        def on_updated(v):
            m = Message.from_variant(v)
            if m.thread_id == thread_id:
                got[m.uid] = m
                poke()

        def on_loaded(tid, _n):
            nonlocal loaded
            if tid == thread_id:
                loaded = True
                poke()

        conv.on_conversation_updated(on_updated)
        conv.on_conversation_loaded(on_loaded)
        try:
            await conv.call_request_conversation(thread_id, 0, count)
            try:
                await asyncio.wait_for(settled.wait(), timeout)
            except TimeoutError:
                pass
        finally:
            conv.off_conversation_updated(on_updated)
            conv.off_conversation_loaded(on_loaded)
            for h in quiet:
                h.cancel()
        return sorted(got.values(), key=lambda m: m.date)[-count:]

    async def send(self, numbers: list[str], text: str) -> None:
        conv = await self._connect()
        addrs = [Variant("(s)", [n]) for n in numbers]
        await conv.call_send_without_conversation(addrs, text, [])

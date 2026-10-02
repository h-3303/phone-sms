"""Contact names from the vCards KDE Connect's contacts plugin syncs to disk."""

import os
import re
from pathlib import Path

VCARD_ROOT = Path.home() / ".local/share/kpeoplevcard"


def digits(number: str) -> str:
    """Comparable key: last 10 digits, so +1 (519) 555-0100 == 5195550100."""
    return re.sub(r"\D", "", number)[-10:]


def load(device_id: str | None = None) -> list[tuple[str, list[str]]]:
    dirs = [VCARD_ROOT / f"kdeconnect-{device_id}"] if device_id else sorted(VCARD_ROOT.glob("kdeconnect-*"))
    out = []
    for d in dirs:
        for f in sorted(d.glob("*.vcf")) if d.is_dir() else []:
            # unfold continuation lines (RFC 6350 §3.2)
            text = re.sub(r"\r?\n[ \t]", "", f.read_text(errors="replace"))
            name, tels = None, []
            for line in text.splitlines():
                key, _, val = line.partition(":")
                key = key.split(";")[0].upper()
                if key == "FN":
                    name = val.strip()
                elif key == "TEL" and val.strip():
                    tels.append(val.strip())
            if name or tels:
                out.append((name or tels[0], tels))
    return out


class Book:
    def __init__(self, device_id: str | None = None):
        self.device_id = device_id
        self._mtime = None
        self._cards: list[tuple[str, list[str]]] = []
        self._by_num: dict[str, str] = {}

    def _refresh(self):
        dirs = [VCARD_ROOT / f"kdeconnect-{self.device_id}"] if self.device_id else VCARD_ROOT.glob("kdeconnect-*")
        mtime = tuple(os.stat(d).st_mtime for d in dirs if d.exists())
        if mtime != self._mtime:
            self._mtime = mtime
            self._cards = load(self.device_id)
            self._by_num = {digits(t): n for n, tels in self._cards for t in tels if digits(t)}

    def name(self, number: str) -> str | None:
        self._refresh()
        return self._by_num.get(digits(number))

    def label(self, number: str) -> str:
        n = self.name(number)
        return f"{n} <{number}>" if n else number

    def search(self, query: str) -> list[tuple[str, list[str]]]:
        self._refresh()
        q = query.lower()
        qd = re.sub(r"\D", "", query)
        return [
            (n, tels) for n, tels in self._cards
            if q in n.lower() or (len(qd) >= 3 and any(qd in re.sub(r"\D", "", t) for t in tels))
        ]

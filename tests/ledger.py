"""The record of Critical messages the test iface saw, and which of them the test expected.

Pure Python (no qgis import), so tests/test_core.py can test it. The plugin's guard writes a Critical
line to the QGIS message log and then to the message bar; the iface records both here.
"""
from typing import List


class Ledger:
    def __init__(self):
        self._entries: List[dict] = []

    def record(self, source: str, text: str) -> None:
        """`source` is "bar" or "log"."""
        self._entries.append({"source": source, "text": text or "", "expected": False})

    def expect(self, fragment: str) -> int:
        """Mark every entry that is not yet expected and contains `fragment`; return how many were marked."""
        marked = 0
        for entry in self._entries:
            if not entry["expected"] and fragment in entry["text"]:
                entry["expected"] = True
                marked += 1
        return marked

    def unexpected(self) -> List[str]:
        return [f"{entry['source']}: {entry['text']}" for entry in self._entries if not entry["expected"]]

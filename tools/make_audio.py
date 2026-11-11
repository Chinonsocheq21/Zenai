"""Record the guided audio sessions in ZenAI's own voice.

    python tools/make_audio.py          # re-record from docs/audio-scripts.md
    python tools/make_audio.py --check  # verify the files and index.json

Each script line is spoken with edge-tts in the app's voice (settings.TTS_VOICE
and TTS_RATE). `[pause N]` lines become N seconds of silence. edge-tts returns
MPEG-2 Layer III at 24 kHz mono 48 kbps: 144-byte frames of 24 ms each. MP3
frames concatenate cleanly, and a frame whose side info and data are all zero
decodes as silence, so no ffmpeg is needed.
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "docs" / "audio-scripts.md"
OUT = ROOT / "src" / "zenai" / "student" / "audio"

TARGET_SECONDS = {"breathe-1min": 60, "notice-3min": 180, "sleep-4min": 240}
HEADER = bytes.fromhex("fff364c4")   # MPEG-2 L3, 48 kbps, 24 kHz, mono, no CRC
FRAME_BYTES = 144
FRAME_SECONDS = 576 / 24000
PAUSE = re.compile(r"^\[pause (\d+(?:\.\d+)?)\]$")
SECTION = re.compile(r"^## ([a-z0-9-]+): (.+)$")


def parse(text: str) -> list[dict]:
    """Sessions from the markdown: id, title and a list of ("say", text) / ("pause", s)."""
    sessions, cur = [], None
    for raw in text.splitlines():
        line = raw.strip()
        m = SECTION.match(line)
        if m:
            cur = {"id": m.group(1), "title": m.group(2), "parts": []}
            sessions.append(cur)
        elif cur is not None and line:
            p = PAUSE.match(line)
            cur["parts"].append(("pause", float(p.group(1))) if p else ("say", line))
    return sessions


def silence(seconds: float) -> bytes:
    frames = max(1, round(seconds / FRAME_SECONDS))
    return (HEADER + bytes(FRAME_BYTES - len(HEADER))) * frames


def frames(data: bytes) -> int:
    """Count MPEG frames by walking the headers (all frames here are 144 bytes,
    or 145 with the padding bit)."""
    i, n = 0, 0
    while i + 4 <= len(data):
        if data[i] != 0xFF or (data[i + 1] & 0xE0) != 0xE0:
            i += 1
            continue
        pad = (data[i + 2] >> 1) & 1
        i += FRAME_BYTES + pad
        n += 1
    return n


def seconds(data: bytes) -> float:
    return frames(data) * FRAME_SECONDS


async def speak(text: str, voice: str, rate: str) -> bytes:
    import edge_tts

    out = b""
    async for chunk in edge_tts.Communicate(text, voice, rate=rate).stream():
        if chunk["type"] == "audio":
            out += chunk["data"]
    return out


async def record() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    from zenai.config import settings

    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for s in parse(SCRIPTS.read_text()):
        audio, words = b"", []
        for kind, val in s["parts"]:
            if kind == "pause":
                audio += silence(val)
            else:
                audio += await speak(val, settings.TTS_VOICE, settings.TTS_RATE)
                words.append(val)
        name = f"{s['id']}.mp3"
        (OUT / name).write_bytes(audio)
        index.append({"id": s["id"], "title": s["title"], "file": name,
                      "seconds": round(seconds(audio)), "transcript": " ".join(words)})
        print(f"{name}: {seconds(audio):.0f} s, {len(audio) / 1024:.0f} KB")
    (OUT / "index.json").write_text(json.dumps({"sessions": index}, indent=2) + "\n")


def check() -> int:
    problems = []
    try:
        index = json.loads((OUT / "index.json").read_text())["sessions"]
    except (OSError, ValueError, KeyError) as e:   # missing or malformed
        print(f"FAIL index.json: {e}")
        return 1
    total = 0
    for sid, target in TARGET_SECONDS.items():
        entry = next((x for x in index if x["id"] == sid), None)
        path = OUT / f"{sid}.mp3"
        if not entry or not path.exists():
            problems.append(f"{sid}: missing")
            continue
        data = path.read_bytes()
        total += len(data)
        got = seconds(data)
        if not (0.75 * target <= got <= 1.25 * target):
            problems.append(f"{sid}: {got:.0f} s, wanted about {target} s")
        if not entry.get("title") or not entry.get("transcript"):
            problems.append(f"{sid}: index entry needs a title and transcript")
        print(f"{sid}: {got:.0f} s (target {target}), {len(data) / 1024:.0f} KB")
    if total > 3 * 1024 * 1024:
        problems.append(f"total {total / 1024 / 1024:.1f} MB is over 3 MB")
    for p in problems:
        print("FAIL", p)
    print("all passed" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check())
    asyncio.run(record())
    sys.exit(check())

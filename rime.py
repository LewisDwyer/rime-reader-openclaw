#!/usr/bin/env python3
"""Rime TTS: Telegram voice notes via the Rime API.

Three modes:
  Document (file/stdin): rime.py <file.txt> [--voice V] [--pause P]
  Single voice (inline): rime.py --text "..." [--voice V]
  Multi-voice (podcast):  rime.py --segments '[...]' [--pause P]
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.request

SAMPLE_RATE = 48000
CHUNK_SIZE = 400  # max characters per API call in document mode


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list:
    """Split text into sentence-aligned chunks under `size` characters."""
    text = " ".join(text.split())

    sentences = []
    for raw in text.replace("! ", ".\n").replace("? ", ".\n").split(".\n"):
        s = raw.strip()
        if s:
            sentences.append(s if s.endswith((".", "!", "?")) else s + ".")

    chunks = []
    current = []
    current_len = 0
    for sentence in sentences:
        if current_len + len(sentence) > size and current:
            chunks.append(" ".join(current))
            current = [sentence]
            current_len = len(sentence)
        else:
            current.append(sentence)
            current_len += len(sentence) + 1
    if current:
        chunks.append(" ".join(current))
    return chunks


def synthesize(text, voice, speed, lang, api_key, model="arcana"):
    """Call Rime TTS API and return raw PCM bytes."""
    body = {
        "text": text,
        "speaker": voice,
        "modelId": model,
        "samplingRate": SAMPLE_RATE,
        "speedAlpha": speed,
    }
    if lang:
        body["lang"] = lang

    req = urllib.request.Request(
        "https://users.rime.ai/v1/rime-tts",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "audio/pcm",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def generate_silence(seconds):
    """Generate silent PCM bytes (16-bit signed LE, mono)."""
    return b"\x00\x00" * int(SAMPLE_RATE * seconds)


def pcm_to_ogg(pcm_data, ogg_path):
    """Convert raw PCM bytes to OGG Opus via ffmpeg."""
    tmp_dir = os.path.dirname(ogg_path)
    pcm_path = os.path.join(tmp_dir, "audio.pcm")
    with open(pcm_path, "wb") as f:
        f.write(pcm_data)

    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "s16le",
            "-ar", str(SAMPLE_RATE),
            "-ac", "1",
            "-i", pcm_path,
            "-c:a", "libopus",
            "-b:a", "64k",
            "-vbr", "on",
            "-application", "voip",
            ogg_path,
        ],
        capture_output=True,
    )
    if result.returncode != 0:
        print(f"ffmpeg error: {result.stderr.decode()}", file=sys.stderr)
        sys.exit(1)
    os.remove(pcm_path)


def main():
    parser = argparse.ArgumentParser(description="Rime TTS")
    parser.add_argument(
        "text_file", nargs="?", default=None,
        help="Path to a text file, or - to read from stdin (document mode)",
    )
    parser.add_argument("--text", default=None,
        help="Inline text to speak (single-voice mode)")
    parser.add_argument("--segments", default=None,
        help='Multi-voice JSON: [{"voice":"atrium","text":"..."},...]')
    parser.add_argument("--voice", default="atrium",
        help="Rime voice ID (default: atrium)")
    parser.add_argument("--speed", type=float, default=1.0,
        help="Speed multiplier (default: 1.0)")
    parser.add_argument("--lang", default=None,
        help="Language code (e.g. eng, fra, spa)")
    parser.add_argument("--pause", type=float, default=0.3,
        help="Silence between chunks/segments in seconds (default: 0.3)")
    args = parser.parse_args()

    if not args.text_file and not args.text and not args.segments:
        parser.error("Provide a text file, --text, or --segments")

    api_key = os.environ.get("RIME_API_KEY")
    if not api_key:
        print("Error: RIME_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    tmp_dir = tempfile.mkdtemp(prefix="rime_")
    ogg_path = os.path.join(tmp_dir, "output.ogg")
    silence = generate_silence(args.pause)
    all_pcm = bytearray()

    if args.segments:
        # Multi-voice podcast mode
        try:
            segments = json.loads(args.segments)
        except json.JSONDecodeError as e:
            print(f"Error parsing --segments JSON: {e}", file=sys.stderr)
            sys.exit(1)

        for i, seg in enumerate(segments):
            text = seg.get("text", "")
            if not text:
                continue
            voice = seg.get("voice", args.voice)
            lang = seg.get("lang", args.lang)
            speed = seg.get("speed", args.speed)
            try:
                pcm = synthesize(text, voice, speed, lang, api_key)
                all_pcm.extend(pcm)
                if i < len(segments) - 1:
                    all_pcm.extend(silence)
            except Exception as e:
                print(f"Error on segment {i} (voice={voice}): {e}", file=sys.stderr)
                sys.exit(1)

    elif args.text_file:
        # Document reading mode — chunk a file or stdin
        if args.text_file == "-":
            text = sys.stdin.read()
        else:
            with open(args.text_file, "r", encoding="utf-8") as f:
                text = f.read()
        text = text.strip()
        if not text:
            print("Error: document is empty", file=sys.stderr)
            sys.exit(1)

        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            try:
                pcm = synthesize(chunk, args.voice, args.speed, args.lang, api_key)
                all_pcm.extend(pcm)
                if i < len(chunks) - 1:
                    all_pcm.extend(silence)
            except Exception as e:
                print(f"Error on chunk {i}: {e}", file=sys.stderr)
                sys.exit(1)

    else:
        # Single-voice inline text mode
        try:
            all_pcm.extend(
                synthesize(args.text, args.voice, args.speed, args.lang, api_key)
            )
        except Exception as e:
            print(f"Error calling Rime API: {e}", file=sys.stderr)
            sys.exit(1)

    pcm_to_ogg(bytes(all_pcm), ogg_path)
    print(ogg_path)


if __name__ == "__main__":
    main()

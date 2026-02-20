#!/usr/bin/env python3
"""Rime Reader: Read a document aloud as a Telegram voice note.

Splits long text into sentence-aligned chunks, synthesizes each with the
Rime TTS API, then stitches the PCM bytes into a single OGG Opus file.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.request

SAMPLE_RATE = 48000
CHUNK_SIZE = 400  # max characters per API call


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list:
    """Split text into sentence-aligned chunks under `size` characters."""
    # Normalise whitespace
    text = " ".join(text.split())

    # Split into sentences
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
    parser = argparse.ArgumentParser(description="Rime document reader")
    parser.add_argument(
        "text_file",
        help="Path to a text file, or - to read from stdin",
    )
    parser.add_argument("--voice", default="luna", help="Rime voice ID")
    parser.add_argument("--speed", type=float, default=1.0, help="Speed multiplier")
    parser.add_argument("--lang", default=None, help="Language code (e.g. eng, fra)")
    parser.add_argument("--pause", type=float, default=0.3, help="Silence between chunks in seconds")
    args = parser.parse_args()

    api_key = os.environ.get("RIME_API_KEY")
    if not api_key:
        print("Error: RIME_API_KEY not set", file=sys.stderr)
        sys.exit(1)

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
    silence = generate_silence(args.pause)

    all_pcm = bytearray()
    for i, chunk in enumerate(chunks):
        try:
            pcm = synthesize(chunk, args.voice, args.speed, args.lang, api_key)
            all_pcm.extend(pcm)
            if i < len(chunks) - 1:
                all_pcm.extend(silence)
        except Exception as e:
            print(f"Error on chunk {i}: {e}", file=sys.stderr)
            sys.exit(1)

    tmp_dir = tempfile.mkdtemp(prefix="rime_reader_")
    ogg_path = os.path.join(tmp_dir, "reading.ogg")
    pcm_to_ogg(bytes(all_pcm), ogg_path)
    print(ogg_path)


if __name__ == "__main__":
    main()

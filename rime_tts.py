#!/usr/bin/env python3
"""Rime TTS: Convert text to OGG Opus audio for Telegram voice notes.

Supports single-voice and multi-voice (stitched) output.
"""

import argparse
import os
import subprocess
import sys
import tempfile
import urllib.request
import json

SAMPLE_RATE = 48000
PAUSE_SECONDS = 0.4


def synthesize(text, voice, model, speed, lang, api_key):
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

    with urllib.request.urlopen(req, timeout=30) as resp:
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
    parser.add_argument("text", nargs="?", default=None, help="Text to convert to speech (single-voice mode)")
    parser.add_argument("--voice", default="luna", help="Rime voice ID")
    parser.add_argument("--model", default="arcana", help="Rime model")
    parser.add_argument("--speed", type=float, default=1.0, help="Speed (1.0 = normal)")
    parser.add_argument("--lang", default=None, help="Language code (e.g. eng, spa, fra)")
    parser.add_argument("--segments", default=None, help='Multi-voice JSON: [{"voice":"luna","text":"Hi"},{"voice":"sirius","text":"Hey"}]')
    parser.add_argument("--pause", type=float, default=PAUSE_SECONDS, help="Pause between segments in seconds (default: 0.4)")
    args = parser.parse_args()

    if not args.text and not args.segments:
        parser.error("Provide either text or --segments")

    api_key = os.environ.get("RIME_API_KEY")
    if not api_key:
        print("Error: RIME_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    tmp_dir = tempfile.mkdtemp(prefix="rime_tts_")
    ogg_path = os.path.join(tmp_dir, "voice.ogg")
    pause = generate_silence(args.pause)

    if args.segments:
        # Multi-voice mode
        try:
            segments = json.loads(args.segments)
        except json.JSONDecodeError as e:
            print(f"Error parsing --segments JSON: {e}", file=sys.stderr)
            sys.exit(1)

        all_pcm = bytearray()
        for i, seg in enumerate(segments):
            text = seg.get("text", "")
            voice = seg.get("voice", args.voice)
            lang = seg.get("lang", args.lang)
            speed = seg.get("speed", args.speed)
            model = seg.get("model", args.model)

            if not text:
                continue

            try:
                pcm = synthesize(text, voice, model, speed, lang, api_key)
                all_pcm.extend(pcm)
                if i < len(segments) - 1:
                    all_pcm.extend(pause)
            except Exception as e:
                print(f"Error on segment {i} (voice={voice}): {e}", file=sys.stderr)
                sys.exit(1)

        pcm_to_ogg(bytes(all_pcm), ogg_path)
    else:
        # Single-voice mode
        try:
            pcm_data = synthesize(args.text, args.voice, args.model, args.speed, args.lang, api_key)
        except Exception as e:
            print(f"Error calling Rime API: {e}", file=sys.stderr)
            sys.exit(1)

        pcm_to_ogg(pcm_data, ogg_path)

    print(ogg_path)


if __name__ == "__main__":
    main()

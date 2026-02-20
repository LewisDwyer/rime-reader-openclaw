# rime-reader

An [OpenClaw](https://openclaw.ai) skill that reads documents aloud as Telegram
voice notes using [Rime TTS](https://rime.ai). Supports three delivery modes:

- **Verbatim** — full text, cleaned and tuned for natural speech
- **Summary** — concise spoken summary
- **Podcast** — two AI hosts break it down in a lively conversation

## Requirements

- [OpenClaw](https://openclaw.ai) installed and configured with a Telegram bot
- A [Rime API key](https://rime.ai)
- `ffmpeg` installed (`brew install ffmpeg` or `apt install ffmpeg`)

## Installation

**1. Copy the skill into your OpenClaw skills directory:**

```bash
git clone https://github.com/LewisDwyer/rime-reader-openclaw ~/.openclaw/skills/rime-reader
```

Or download and copy the folder manually to `~/.openclaw/skills/rime-reader/`.

**2. Set your Rime API key** (add to `.bashrc` / `.zshrc` / your env):

```bash
export RIME_API_KEY=your_key_here
```

**3. Register the skill** in `~/.openclaw/openclaw.json`:

```json
"skills": {
  "entries": {
    "rime-reader": { "enabled": true }
  }
}
```

**4. Add a trigger to your `~/.openclaw/workspace/SOUL.md`:**

```markdown
## Document Reading

When the user sends a file or pastes text and asks you to read it, use the
`rime-reader` skill. It handles everything: mode selection (verbatim, summary,
or podcast), voice selection, text normalization, and audio generation.

**Comparison demos:** run both `rime-reader` and `openai-tts` on the same text
and label the results "Rime _(voice name)_:" and "OpenAI:" above each MEDIA
directive.
```

**5. Restart your OpenClaw gateway:**

```bash
openclaw gateway restart
```

## Usage

Send a document or paste text into your Telegram bot and ask it to be read.
If you don't specify a mode, the bot will ask:

> How would you like this delivered?
>
> 📖 **Verbatim** — full text, cleaned and tuned for Rime
> 📋 **Summary** — concise spoken summary
> 🎙️ **Podcast** — two hosts break it down in a lively conversation

For verbatim and summary modes, you'll also be prompted to pick a voice.

## Voices

Default: `atrium`. Recommended picks:

| Voice | Character |
|-------|-----------|
| `atrium` | Steady, polished, confident |
| `lyra` | Smooth, expressive, quietly intense |
| `transom` | Deep, resonant, commanding |
| `parapet` | Cool, measured, precise |
| `fern` | Warm, natural, approachable |
| `thalassa` | Rich, textured, distinctive |
| `truss` | Firm, clear, authoritative |
| `sirius` | Crisp, formal, reliable |
| `eliphas` | Smooth, deep, gravitas |
| `lintel` | Deliberate, focused, clean |

## How it works

`rime.py` is a single script with three modes:

- **Verbatim / Summary** — splits the text into sentence-aligned chunks,
  synthesizes each with the Rime API, stitches the PCM audio, and encodes to
  OGG Opus via ffmpeg.
- **Podcast** — synthesizes each host's lines separately using `--segments`
  and stitches them into a single voice note.
- All text normalization (markup removal, symbol replacement, prosody tuning)
  is done by the LLM before the script is called.

## Comparing Rime vs OpenAI TTS

If you also have the `openai-tts` skill installed, ask the bot to "compare"
and it will return both a Rime and an OpenAI voice note side by side.

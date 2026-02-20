---
name: rime-reader
description: Read a document or block of text aloud as a Telegram voice note using Rime TTS. Supports verbatim, summary, and podcast (multi-host) modes. Handles long documents by chunking and stitching.
metadata: {"openclaw":{"requires":{"env":["RIME_API_KEY"],"bins":["ffmpeg"]},"primaryEnv":"RIME_API_KEY"}}
---

# Rime Reader

Use this skill to read a document or block of text aloud. It supports three
delivery modes — verbatim, summary, and podcast — and handles all text
normalization, voice selection, and audio generation.

## When to use

- When the user sends a file or pastes text and asks you to read it
- When the user asks for a summary read aloud
- When the user wants a podcast-style breakdown of a document
- When producing a spoken Rime reading to compare against default TTS

## Workflow

### Step 1 — Ask for the delivery mode (if not specified)

If the user hasn't indicated how they want the material delivered, ask:

> How would you like this delivered?
>
> 📖 **Verbatim** — full text, cleaned and tuned for Rime
> 📋 **Summary** — concise spoken summary
> 🎙️ **Podcast** — two hosts break it down in a lively conversation

### Step 2 — For verbatim or summary: ask for a voice

> Which voice should I use?
>
> 🏛️ **atrium** — steady, polished, confident (default)
> ✨ **lyra** — smooth, expressive, quietly intense
> 🌊 **transom** — deep, resonant, commanding
> 🧊 **parapet** — cool, measured, precise
> 🌿 **fern** — warm, natural, approachable
> 🌑 **thalassa** — rich, textured, distinctive
> 🔩 **truss** — firm, clear, authoritative
> 🔷 **sirius** — crisp, formal, reliable
> 🌒 **eliphas** — smooth, deep, gravitas
> 📐 **lintel** — deliberate, focused, clean
>
> Reply with a name, or say "surprise me" for a random pick.

For **podcast mode**, skip voice selection — you choose the voices (see Step 4b).

### Step 3 — Normalize and tune the text

Before generating audio, you must clean and rewrite the text so it sounds
natural when spoken. The scripts do no text processing — this is your job.

#### Remove markup and structure

| What to remove | How |
|----------------|-----|
| Markdown headers (`# Title`) | Keep the heading text, remove the `#` |
| Bold / italic (`**x**`, `_x_`) | Keep the text, remove the markers |
| Strikethrough (`~~x~~`) | Remove entirely — the content was deleted |
| Inline code (`` `x` ``) | Remove or replace with a plain-English description |
| Fenced code blocks (` ``` `) | Remove entirely — code syntax is unreadable as speech |
| Markdown links — `[text]` + `(url)` | Keep display text only, drop the URL |
| Markdown images — `![alt]` + `(url)` | Remove entirely |
| Footnote/citation refs (`[1]`, `[^2]`) | Remove |
| HTML tags (`<br>`, `<em>`) | Remove |
| HTML entities (`&amp;`, `&nbsp;`) | Expand: `&amp;` → "and", `&nbsp;` → space, etc. |
| Horizontal rules (`---`, `***`) | Remove |
| Bullet markers (`•`, `-`, `*`, `1.`) | Remove — the sentence will read fine without them |
| Table rows (`\| col \| col \|`) | Rewrite the key information as a sentence; don't just delete |

#### Fix symbols

Rime reads most symbols literally, which sounds bad. Replace them:

| Symbol | Replace with |
|--------|-------------|
| `→` `←` `↑` `↓` | "to", "from", "up", "down" |
| `≥` `≤` `≠` `≈` | "or more", "or less", "is not", "approximately" |
| `×` `÷` `±` | "times", "divided by", "plus or minus" |
| `©` `®` `™` | Remove |
| `…` | `...` (Rime reads ellipsis as a trailing pause) |
| `–` (en dash, e.g. date ranges) | `, ` — the comma gives a natural pause |

**Keep** the em dash `—`. Rime uses it as a prosodic break, equivalent to a
meaningful pause mid-sentence.

#### Fix text that Rime misreads

| Issue | Problem | Fix |
|-------|---------|-----|
| URLs (`https://...`, `www....`) | Read as "H T T P S colon slash slash..." | Remove entirely |
| ALL CAPS words (`IMPORTANT`, `WARNING`) | Read as a single word like a name | Rewrite as title case: `Important`, `Warning` |
| Initialisms (`API`, `SDK`, `UI`, `LLM`) | May be read as a word | Write as `A.P.I.`, `S.D.K.`, `U.I.`, `L.L.M.` — or spell out in full |
| Known acronyms (`NASA`, `DNA`, `FBI`) | Rime handles these correctly | Leave as-is |
| Numbers in code format (`1_000_000`, `0x1F`) | Read literally | Rewrite as words: "one million", "thirty-one" |
| Formulas / equations | Read as symbol names | Rewrite in plain words |
| Currency (`$`, `€`, `£`) | Rime handles `$` and `%` correctly | Leave as-is; write out `€` as "euros", `£` as "pounds" |

#### Punctuation controls how Rime speaks

Punctuation is not just grammar — it directly shapes rhythm, intonation, and
pacing:

| Punctuation | Effect |
|-------------|--------|
| `.` | Statement with a longer pause after |
| `,` | Slight pause, keeps the sentence flowing |
| `?` | Rising intonation |
| `!` | Emphasis / excitement |
| `?!` | Excited question |
| `...` | Trailing off |
| `—` | Abrupt break or meaningful aside |

When rewriting for spoken delivery:
- Break long compound sentences into shorter ones — each period is a breath point
- Add commas to control pacing within sentences
- Use contractions ("don't", "it's") — they sound more natural than "do not", "it is"
- Remove or reword anything that only makes sense visually (e.g. "see Figure 3", "as shown above")

#### Read the room — tune for content type

Before rewriting, identify what kind of content this is and what emotional
register it belongs to. Getting this wrong produces something that sounds
technically clean but emotionally wrong.

| Content type | Examples | Goal |
|---|---|---|
| **Informational** | Technical docs, reports, summaries | Clear and easy to follow — not flat, but not dramatic |
| **Narrative / storytelling** | Blog posts, essays, case studies | Draw the listener in — pace it like someone telling a story |
| **Emotive / personal** | Speeches, tributes, letters, poetry | Let the emotion breathe — don't over-punctuate, trust the words |
| **Promotional / persuasive** | Marketing copy, pitches, product launches | Energy and conviction — rhetorical questions, emphasis on key claims |
| **Serious / formal** | Legal, medical, official statements | Measured and authoritative — no flourishes, just clarity and weight |
| **Conversational** | Interviews, transcripts, casual articles | Relaxed rhythm, contractions, natural pauses |

**Informational** — Clear and flowing. Vary sentence length. Commas for pacing,
periods for clarity. The listener should feel informed, not lectured.

**Narrative / storytelling** — This is where Rime shines. Use the full range:
em dashes for reveals, `...` for suspense, short punchy sentences after
build-up, rhetorical questions to create engagement.

**Emotive / personal** — Don't over-engineer it. Short sentences at key
moments. A `—` where a speaker would pause before saying something difficult.
`...` where a thought trails off with feeling. Resist the urge to add `!` —
that cheapens it. "She worked tirelessly — for decades." not "She worked
tirelessly for decades!"

**Promotional / persuasive** — Lean into energy. `!` on genuine claims, not
fluff. `?!` on excited questions. Short punchy statements after rhetorical
build-up. Forward momentum — the listener should feel something building.

**Serious / formal** — No em dashes as dramatic devices. No ellipsis. Clean
sentence structure, deliberate pacing via commas and sentence length. The
gravity comes from the content.

**Conversational** — Contractions everywhere. Short sentences. Comma-heavy for
natural breath patterns. Should sound like someone talking, not reading.

**All types:** Vary sentence length. A string of identical-length sentences
sounds robotic. Short sentences hit hard. Longer sentences, with commas placed
for breath, carry the listener through context before landing on the point. Mix
them.

### Step 4a — Verbatim or summary: write to temp file and run rime_reader.py

Write the tuned text to a temp file:

```python
import tempfile
p = tempfile.mktemp(suffix='.txt')
open(p, 'w').write("""TUNED TEXT GOES HERE""")
print(p)
```

Then run:

    python3 {baseDir}/rime.py /path/to/file.txt --voice <chosen>

The script prints the path to the generated `.ogg` file.

### Step 4b — Podcast mode: write the script and run rime_tts.py

Skip the voice selection prompt — assign voices yourself.

Write a two-host podcast script that genuinely discusses the material. The
hosts should feel like real people, not two voices alternating summaries.

**Host A — the explainer.** Knowledgeable, clear, keeps the conversation on
track. Use `atrium` or `transom`.

**Host B — the curious one.** Asks the questions the listener is thinking,
reacts to surprising points, brings energy. Use `lyra` or `fern`.

What makes a good podcast script:
- Hosts introduce themselves and the topic right away — no cold start
- They discuss and react, not recite — Host B pushes back, expresses surprise,
  asks "wait, but why?" — that's what makes it listenable
- Key ideas get unpacked through conversation, not monologue
- Short turns (2–5 sentences each) keep the pacing tight
- Light humour is welcome where the content allows it
- End with a clear takeaway or closing exchange, not just a trailing off

Build the script as a `--segments` JSON array and run:

    python3 {baseDir}/rime.py --segments '[
      {"voice": "atrium", "text": "..."},
      {"voice": "lyra",   "text": "..."},
      ...
    ]' --pause 0.4

The script prints the path to the generated `.ogg` file.

### Step 5 — Return the audio

    MEDIA: /path/to/reading.ogg
    [[audio_as_voice]]

## Script options (rime.py)

- `--voice VOICE` — Rime voice ID (default: `atrium`). Always pass the voice
  the user selected. In podcast mode, set per segment in the JSON.
- `--speed SPEED` — Speed multiplier (default: `1.0`)
- `--lang LANG` — Language code for non-English text (e.g. `fra`, `spa`)
- `--pause SECS` — Silence between chunks or segments in seconds
  (default: `0.3`; use `0.4` for podcast mode to give speaker turns more room)
- `--segments JSON` — Multi-voice JSON array (podcast mode)
- `--text TEXT` — Inline text to speak (single short utterance)

**Model:** always `arcana`. There is no `--model` flag.

## Comparison mode

To demo Rime vs the default, run `rime-reader` and `openai-tts` on the same
text and return both MEDIA directives with labels:

    Rime _(atrium)_:
    MEDIA: /path/to/rime.ogg
    [[audio_as_voice]]

    OpenAI:
    MEDIA: /path/to/openai.ogg
    [[audio_as_voice]]

## Available voices (Arcana model)

Recommended: `atrium` (default), `lyra`, `transom`, `parapet`, `fern`,
`thalassa`, `truss`, `sirius`, `eliphas`, `lintel`

Full list: luna, lyra, astra, mars, sirius, vespera, estelle, moss, fern,
walnut, bond, arcade, albion, truss, stucco, transom, pilaster, masonry,
oculus, lintel, atrium, cupola, parapet, eliphas, eucalyptus, marlu, vashti
(and many more — see `rime-tts` skill for the full Arcana English voice list).

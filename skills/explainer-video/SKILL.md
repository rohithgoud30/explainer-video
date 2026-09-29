---
name: explainer-video
description: Make a narrated, captioned explainer video (MP4) from a slide script, free, on your own machine. Use when asked to make a video, video tutorial, walkthrough, or step-by-step explainer of a tool, API, concept, or codebase.
argument-hint: <what the video should explain>
---

# Explainer video

Renders slides + a free, offline voice (Kokoro 82M) + captions into a 1920x1080 MP4. Each slide element can appear, highlighted, on the exact sentence that mentions it. The renderer (`render.py`) ships in this skill's folder and runs with `uv`. On its first run it downloads everything else by itself: its Python packages, ffmpeg, the voice model (~340 MB), and Chromium if Google Chrome isn't installed. After that it works offline. No API key, no account, no cloud voice service. If Kokoro can't run, the renderer prints `Kokoro failed … using edge-tts Ava instead` and voices the whole video with edge-tts (online, free); say so when you report the result. Below, `<skill>` means the folder that holds this SKILL.md.

What to explain: $ARGUMENTS. If that is empty, use the user's request. If there is no request either, ask what the video should explain, and ask nothing else.

## Steps

1. **uv ready.** `uv --version`. If it fails, install uv with `curl -LsSf https://astral.sh/uv/install.sh | sh` (or `brew install uv`), then open a new shell. Done when `uv --version` prints a version. uv is the only thing to install.
2. **Facts gathered.** Read the real source (official docs, the codebase, `--help`) for everything the video will claim. Every command, URL, number, and code sample on a slide comes from that source.
3. **Story written.** Before any JSON, write the one sentence the viewer should be able to repeat afterwards. Then plan the slides in the story order below. Done when every slide serves that sentence.
4. **Script written.** Write `videos/<topic>/script.json` (schema below), relative to the current directory unless the user names another location. Pick `<topic>` yourself from the subject, short and kebab-case, like `jev` or `react-server-components`. If `videos/<topic>/` already exists, add `-2`, `-3`, and so on, so an existing video is never overwritten. Give every visual element a `data-at` so it appears when the voice says it.
5. **Wait-what pass.** Read every `say` line in order, as a viewer who has never heard of the topic. For each line, ask: would this land the first time? A line fails when it uses a term before explaining it, needs a fact that comes later, or breaks a narration rule below. Re-pitch each failing line: add the missing context, then say it again in simpler words. Done when a full read-through has no failing line.
6. **Rendered.** `uv run <skill>/render.py videos/<topic>/script.json videos/<topic>/<topic>.mp4`. It takes about as long as the video plays; the first run also spends a few minutes downloading.
7. **Checked.** The render saves the last frame of every slide as `videos/<topic>/check/slide-NN.png`. Look at each one. Done when no content touches the caption band at the bottom, nothing wraps awkwardly, and every code sample is readable. Fix `script.json` and re-render until then. Delete `videos/<topic>/check/` afterwards.

## Story order

The viewer has to feel the problem before the answer means anything.

1. **The problem**, as one concrete example the viewer can picture (a real message, file, or error).
2. **The obvious fixes and why they fail.** One slide each, with the failure shown on screen.
3. **What it is.** It fills the gap the fixes left. Say it in one plain sentence.
4. **How it works**, using the same example from slide 1.
5. **The one rule** that matters most for good results.
6. **Try it:** the minimum real steps and code.
7. **Recap:** repeat the one sentence from step 3, plus what it does *not* do.

## Script schema

```json
{
  "voice": "af_heart",
  "speed": 0.75,
  "pronounce": { "ASAP": "A-sap", "docs.example.com": "docs dot example dot com" },
  "slides": [
    {
      "label": "The problem",
      "title": "Your code can't read",
      "code": "optional, always visible, escaped for you",
      "body": "<div class=flow><div class=good data-at=1>A person<small>knows in one second</small></div><div class=bad data-at=2>Your code<small>sees a string</small></div></div>",
      "say": ["Imagine this message arrives.", "A person gets it instantly.", "Your code just sees characters."]
    }
  ]
}
```

- `pronounce`: words the voice would misread, and what to say instead. Only the voice changes; captions still show the original word.
- `say`: one sentence per entry. Each is spoken and captioned on its own. Put 4–8 on each slide and aim for 3–5 minutes in total.
- `data-at=N` on any element in `body` hides it until sentence N (counting from 0). While sentence N plays, the element slides in with a yellow outline, then stays on screen. Elements without `data-at` show from the start.
- `code`: plain text in a code box above `body`, always visible. To reveal code at a sentence, put `<pre data-at=N>` in `body` instead, and escape `<`, `>`, and `&`.
- Room for content ends about 940px from the top. Keep a code box to 11 lines or fewer, and a slide to about 3 blocks.

### Body parts

| Markup | Use for |
| --- | --- |
| `<div class=chat><div class=them>…</div><div class=me>…</div></div>` | messages, a chatbot reply |
| `<div class=flow><div>A<small>detail</small></div><div class=arrow>→</div><div class=good>B</div></div>` | side-by-side comparisons, before → after (`good` = mint border, `bad` = coral border) |
| `<div class='meter good' style='--p:.95'><span>name</span><div class=track><div class=fill></div></div><b>0.95</b><span>meaning</span></div>` | probabilities, scores, percentages (`good`, `bad`, or `mid` = yellow) |
| `<div class=cols><div>left</div><div>right</div></div>` | steps on the left, code on the right |
| `<table>` with `<tr data-at=N>` | kinds, options, one row per sentence |
| `<p class=big>`, `<p class=muted>`, `class=bad` / `class=good` on text | the key sentence, side notes, wrong / right |

Colours carry meaning: coral = broken or wrong, mint = works, yellow = what is being said now. Use one emoji at most on a heading, and only as an icon.

## Narration

The bar: a viewer who knows nothing about the topic follows every sentence the first time. The wait-what pass (step 5) enforces it.

- Give context before detail: say what a thing is for before its name or its syntax.
- Write in ASD-STE100 Simplified Technical English: common words, active voice, one idea per sentence, 20 words or fewer, and the same word for the same thing every time.
- Use the subject's own terms. If the topic has a `CONTEXT.md` (follow `CONTEXT-MAP.md` when there are several), take the words from it; otherwise use the official docs' words. Define each term once, when it first appears.
- Talk to one person: "you", contractions, a warm tone.
- Say what the screen shows, in the same order.
- Write `say` lines exactly as the caption should read: "ASAP", "docs.typesafe.ai", `TYPESAFE_API_KEY`. Never space out letters ("A S A P"); voices read them one by one.
- Put every word a voice would misread into `pronounce`: acronyms said as words, respelled so the voice says them as people do ("ASAP": "A-sap"), web addresses, identifiers, and brand names. Write decimals as words in `say` ("zero point nine five").
- `voice` is a Kokoro voice. `af_heart` (default, warm female) is the most natural; others: `af_bella`, `am_michael`, `am_fenrir` (US), `bf_emma`, `bm_george` (UK). `speed` 0.75 (default) is a calm teaching pace; Kokoro's normal 1.0 feels rushed.

## Example

`<skill>/example.json` is a complete script in this story order (a video about Jev from TypeSafe).

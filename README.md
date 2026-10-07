# explainer-video

An agent skill that makes narrated, captioned explainer videos for free. The voice comes from [Kokoro 82M](https://huggingface.co/hexgrad/Kokoro-82M) (open weights, Apache 2.0) and runs offline, with Microsoft's free edge-tts Ava voice as a backup if Kokoro can't run, Chromium renders the slides, and ffmpeg puts it together, all on your own machine. The skill folder holds everything it needs, so any agent that installs it can render videos.

## Install

```sh
npx skills add rohithgoud30/explainer-video
```

The only other thing it needs is [uv](https://docs.astral.sh/uv/): `curl -LsSf https://astral.sh/uv/install.sh | sh`. The first video downloads the rest by itself: ffmpeg, the voice model, and Chromium if you don't have Google Chrome.

## Use

| Agent | Type |
| --- | --- |
| Claude Code | `/explainer-video how to use Jev from TypeSafe` |
| Codex | `$explainer-video how to use Jev from TypeSafe` |
| Any agent | `Make a video explaining how to use Jev from TypeSafe` |

The agent picks the video's name itself, researches the topic, writes the script, renders the video, and checks the frames. You get `videos/<name>/script.json` and `videos/<name>/<name>.mp4` in your current folder.

## By hand

```sh
uv run skills/explainer-video/render.py skills/explainer-video/example.json videos/example/example.mp4
```

The script format is documented in [`skills/explainer-video/SKILL.md`](skills/explainer-video/SKILL.md), and [`example.json`](skills/explainer-video/example.json) is a full example.

To show a real source page in a video (docs, an article, an online book), screenshot it and put the image on a slide:

```sh
uv run skills/explainer-video/capture.py https://example.com/docs/page videos/example/shots/page.png --dark
uv run skills/explainer-video/capture.py https://example.com/docs/page videos/example/shots/part.png --dark --section "Heading text"
```

The first shot starts at the page's title. The second is cropped to the section under that heading. Both skip site headers, ads, and cookie popups.

Every video has chapters: one per slide, named by the slide's title and stored in the MP4, so players can show the parts and jump between them.

Acronyms are read letter by letter automatically (HTML is said "H-T-M-L"), so scripts don't need to spell them out.

The skill's wait-what pass is adapted from the `wait-what` skill in [Matt Pocock's skills](https://github.com/mattpocock/skills) (MIT); see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).


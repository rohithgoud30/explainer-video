# explainer-video

An agent skill that turns `videos/<topic>/script.json` into `videos/<topic>/<topic>.mp4`: slides rendered by Chromium, a free offline Kokoro 82M voice, captions, and ffmpeg, run with `uv`. Everything ships in `skills/explainer-video/`, so an installed skill can render on its own.

## Making a video

Use the `explainer-video` skill (`skills/explainer-video/SKILL.md`). It is the single source for the script schema, story order, body parts, and narration style. `skills/explainer-video/example.json` is the reference script.

## Changing the renderer

- `skills/explainer-video/render.py` is the whole renderer. Its dependencies, ffmpeg included (via `imageio-ffmpeg`), live in its inline `# /// script` header, so `uv run` is the only setup. Keep it that way: users install nothing but uv.
- A change is verified when `uv run skills/explainer-video/render.py skills/explainer-video/example.json videos/example/example.mp4` succeeds and frames pulled from each slide still look right: nothing touches the caption band, and reveals and highlights land on the right sentence.
- A new body part (CSS class) gets a row in the skill's "Body parts" table in the same change, so agents know it exists.
- Colours carry meaning across every video: coral = broken or wrong, mint = works, yellow = what is being said now. New styles keep those meanings.

## Layout

- `skills/explainer-video/` is the skill and its renderer, and the only copy of both. Users install it with `npx skills add rohithgoud30/explainer-video`.
- `videos/` is local output only and is git-ignored. Rendered videos are never committed.

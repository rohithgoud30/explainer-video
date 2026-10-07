# /// script
# requires-python = ">=3.11"
# dependencies = ["kokoro-onnx", "soundfile", "edge-tts", "playwright", "imageio-ffmpeg"]
# ///
"""Turn a slide script (JSON) into a narrated, captioned MP4.

Usage: render.py videos/<topic>/script.json [OUT.mp4]   (default: videos/<topic>/<topic>.mp4)
Voice: Kokoro 82M (open weights, Apache 2.0), run offline with kokoro-onnx.
If Kokoro can't run, the whole video falls back to edge-tts (Microsoft's free online voice, Ava).
"""
import asyncio
import base64
import html
import mimetypes
import os
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

import imageio_ffmpeg
import soundfile
from playwright.sync_api import sync_playwright

FPS = 30
# Acronyms people say as a word, so they are not spelled out letter by letter. Add to "pronounce" for others.
SAID_AS_WORDS = {"ASAP", "NASA", "JSON", "DOM", "GIF", "JPEG", "TODO", "SCSS", "CORS", "CRUD", "REST", "YAML", "WASM"}

KOKORO_URL ="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
KOKORO_FILES = ("kokoro-v1.0.onnx", "voices-v1.0.bin")
KOKORO_DIR = pathlib.Path(os.environ.get("KOKORO_DIR", pathlib.Path.home() / ".cache" / "explainer-video"))
ANIM_FRAMES = 14  # frames captured for each reveal (~0.47s)

FONTS = ("<link rel=stylesheet href='https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400"
         "&family=IBM+Plex+Mono:wght@400;600&display=block'>")

CSS = """
:root{--bg:#1b2836;--grid:rgba(255,255,255,.045);--ink:#f2efe6;--muted:#9fb0c2;--hl:#ffd84d;--bad:#ff8a7a;--good:#72e0b0;--card:#22344a;--line:#36506c}
*{box-sizing:border-box;margin:0}
body{width:1920px;height:1080px;overflow:hidden;color:var(--ink);font:36px/1.45 'Atkinson Hyperlegible',system-ui,sans-serif;
  background:var(--bg);background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px);background-size:48px 48px}
.slide{padding:84px 130px 180px;height:100%}
.label{color:var(--muted);font-size:30px}
h1{font-size:74px;line-height:1.1;margin:6px 0 44px;letter-spacing:-.5px}
p{margin:22px 0;max-width:1500px}
.big{font-size:54px;line-height:1.25;font-weight:700}
.muted{color:var(--muted)}
.bad{color:var(--bad)}.good{color:var(--good)}
b,strong{font-weight:700}
code,pre{font-family:'IBM Plex Mono',Menlo,monospace}
code{color:var(--hl);font-size:.9em}
pre{background:#132030;border:2px solid var(--line);border-radius:14px;padding:28px 36px;font-size:27px;line-height:1.45;color:#d7e3ef;white-space:pre-wrap;margin-bottom:26px}
ol,ul{padding-left:48px}li{margin:16px 0;padding-left:6px}
table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:20px 26px;border-bottom:2px solid var(--line);vertical-align:top}th{color:var(--muted);font-weight:400}
.flow{display:flex;align-items:stretch;gap:36px;margin:24px 0 36px}
.flow>div{flex:1;background:var(--card);border:3px solid var(--line);border-radius:22px;padding:34px 36px;font-size:42px;font-weight:700;line-height:1.2}
.flow>div small{display:block;margin-top:14px;font-size:30px;font-weight:400;color:var(--muted);line-height:1.35}
.flow>div.bad{border-color:var(--bad)}.flow>div.good{border-color:var(--good)}
.flow>.arrow{flex:0;align-self:center;background:none;border:0;padding:0;font-size:64px;color:var(--muted)}
.cols{display:grid;grid-template-columns:1fr 1.6fr;gap:56px;align-items:start}
.icon{font-size:64px;line-height:1;margin-bottom:18px;display:block}
.chat{display:flex;flex-direction:column;gap:24px;max-width:1300px;margin-bottom:30px}
.chat>div{padding:24px 36px;border-radius:32px;max-width:900px;font-size:40px;line-height:1.35}
.me{align-self:flex-end;background:#3d63d8}.them{align-self:flex-start;background:var(--card);border:2px solid var(--line)}
.meter{color:var(--ink)!important;display:flex;align-items:center;gap:28px;font-size:40px;margin:18px 0}
.meter .track{width:560px;height:30px;border-radius:15px;background:#132030;border:2px solid var(--line);overflow:hidden}
.meter .fill{height:100%;width:calc(var(--p) * 100%);background:var(--ink)}
.meter.good .fill{background:var(--good)}.meter.bad .fill{background:var(--bad)}.meter.mid .fill{background:var(--hl)}
.meter>span:first-child{min-width:230px;white-space:nowrap}.meter>span:last-child{color:var(--muted)}
.meter b{width:120px;font-family:'IBM Plex Mono',monospace}
[data-at]{opacity:0}
[data-at].shown{opacity:1}
tr[data-at]:not(.shown)>td{border-color:transparent}  /* collapsed table borders ignore row opacity */
.now{outline:4px solid var(--hl);outline-offset:10px;border-radius:14px;animation:enter .45s cubic-bezier(.2,.7,.2,1) both}
.slide.enter{animation:fade .4s ease-out both}
@keyframes enter{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
.cap{position:fixed;left:0;right:0;bottom:46px;text-align:center}
.cap span{display:inline-block;max-width:1640px;background:rgba(10,16,24,.88);color:#fff;font-size:38px;line-height:1.35;padding:14px 32px;border-radius:14px}
.bar{position:fixed;left:0;bottom:0;height:8px;background:var(--hl)}
.shot{margin:0;display:flex;flex-direction:column;align-items:flex-start;gap:14px}
.shot img{display:block;max-width:100%;max-height:600px;border-radius:14px;border:2px solid var(--line);box-shadow:0 18px 50px rgba(0,0,0,.45)}
.shot figcaption{font-size:24px;color:var(--muted)}
"""

STEP_JS = """([j, caption]) => {
  document.querySelectorAll('[data-at]').forEach(e => {
    const at = +e.dataset.at;
    e.classList.toggle('shown', at <= j);
    e.classList.toggle('now', at === j);
  });
  document.querySelector('.cap span').textContent = caption;
}"""


def ff(*args):  # ffmpeg ships inside the imageio-ffmpeg package, so nothing to install
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", *args], check=True)


def duration(path):
    return soundfile.info(str(path)).duration


def inline_images(body, base):
    """Slides load as page content with no file access, so local <img src> files are embedded as data URIs.
    Paths are relative to the script.json folder; web URLs and data URIs are left alone."""
    def embed(m):
        path = base / m.group(3)
        mime = mimetypes.guess_type(path.name)[0] or "image/png"
        return f'{m.group(1)}"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"'
    # Only real <img> tags: code samples on a slide can contain text like src="script.js".
    return re.sub(r"""(<img\b[^>]*?\bsrc=)(["']?)(?!data:|https?:)([^"'\s>]+)\2""", embed, body)


def slide_html(slide, progress, base):
    code = f"<pre>{html.escape(slide['code'])}</pre>" if slide.get("code") else ""
    return (f"<!doctype html><meta charset=utf-8>{FONTS}<style>{CSS}</style>"
            f"<div class='slide enter'><div class=label>{slide.get('label', '')}</div><h1>{slide.get('title', '')}</h1>"
            f"{code}{inline_images(slide.get('body', ''), base)}</div>"
            f"<div class=cap><span></span></div><div class=bar style='width:{progress}%'></div>")


def speakable(line, pronounce):
    """What the voice says for a caption line: "pronounce" swaps first, then leftover acronyms are spelled out."""
    for word, say in pronounce.items():
        line = re.sub(rf"(?<!\w){re.escape(word)}(?!\w)", say, line)
    # Any acronym left is spelled letter by letter with hyphens: HTML -> "H-T-M-L", APIs -> "A-P-I's".
    # Hyphens give every letter full stress so the voice says it clearly instead of slurring it;
    # the apostrophe makes the plural "eyes", not "is". Acronyms said as words stay as they are.
    def letters(m):
        word, plural = m.group(1), m.group(2)
        return m.group(0) if word in SAID_AS_WORDS else "-".join(word) + ("'s" if plural else "")
    return re.sub(r"(?<![\w-])([A-Z]{2,6})(s?)(?![\w-])", letters, line)


def render(script_path, out_path):
    script = json.loads(pathlib.Path(script_path).read_text())
    voice, speed = script.get("voice", "af_heart"), script.get("speed", 0.75)
    # "pronounce": {"ASAP": "A-sap"} changes only what the voice hears; captions keep the original
    pronounce = script.get("pronounce", {})

    spoken = lambda line: speakable(line, pronounce)
    slides = script["slides"]
    # one item per spoken sentence: (key, slide index, sentence index, sentence, last in slide)
    items = []
    for i, s in enumerate(slides):
        say = s["say"] if isinstance(s["say"], list) else [s["say"]]
        items += [(f"{i:03d}_{j:03d}", i, j, line, j == len(say) - 1) for j, line in enumerate(say)]

    work = pathlib.Path(tempfile.mkdtemp(prefix="explainer-"))
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from kokoro_onnx import Kokoro

        KOKORO_DIR.mkdir(parents=True, exist_ok=True)
        for name in KOKORO_FILES:  # downloaded once (~340 MB), then reused offline
            if not (KOKORO_DIR / name).exists():
                urllib.request.urlretrieve(KOKORO_URL + name, KOKORO_DIR / name)
        kokoro = Kokoro(*(str(KOKORO_DIR / name) for name in KOKORO_FILES))
        for key, _, _, line, _ in items:
            samples, rate = kokoro.create(spoken(line), voice=voice, speed=speed, lang="en-us")
            soundfile.write(work / f"{key}.voice.wav", samples, rate)
        voice_ext = ".wav"
    except Exception as err:  # one voice per video: redo every line with the backup
        print(f"Kokoro failed ({err!r}); using edge-tts Ava instead", file=sys.stderr)
        import edge_tts

        async def speak_all():
            for key, _, _, line, _ in items:
                await edge_tts.Communicate(spoken(line), "en-US-AvaMultilingualNeural", rate="-4%").save(str(work / f"{key}.voice.mp3"))

        asyncio.run(speak_all())
        voice_ext = ".mp3"

    frames, wavs = [], []  # frames: (png name, seconds on screen)
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(channel="chrome")  # installed Google Chrome
        except Exception:  # no Chrome: fetch Playwright's own Chromium once
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        for key, i, j, line, last in items:
            if j == 0:
                page.set_content(slide_html(slides[i], 100 * (i + 1) / len(slides), pathlib.Path(script_path).parent),
                                 wait_until="networkidle")
                page.evaluate("document.fonts.ready")
            page.evaluate(STEP_JS, [j, line])

            lead, tail = (0.5 if j == 0 else 0), (1.0 if last else 0.7)  # breath between sentences and slides
            wav = work / f"{key}.wav"
            ff("-i", str(work / f"{key}.voice{voice_ext}"), "-af", f"adelay={int(lead * 1000)}|{int(lead * 1000)},apad=pad_dur={tail}",
               "-ar", "48000", "-ac", "2", str(wav))
            wavs.append(f"file '{wav.name}'")
            total = duration(wav)

            # step through the reveal animation frame by frame, then hold the settled frame
            animated = page.evaluate("document.getAnimations().length") > 0
            n = ANIM_FRAMES if animated else 0
            for f in range(n):
                page.evaluate(f"document.getAnimations().forEach(a => {{ a.pause(); a.currentTime = {f * 1000 / FPS}; }})")
                page.screenshot(path=work / f"{key}_{f:02d}.png")
                frames.append((f"{key}_{f:02d}.png", 1 / FPS))
            page.evaluate("document.getAnimations().forEach(a => a.cancel())")  # settled styles; won't replay later
            page.screenshot(path=work / f"{key}.png")
            frames.append((f"{key}.png", total - n / FPS))
        browser.close()

    (work / "audio.txt").write_text("\n".join(wavs) + "\n")
    # concat demuxer needs the last image listed twice to honour its duration
    (work / "video.txt").write_text("".join(f"file '{p}'\nduration {d:.4f}\n" for p, d in frames) + f"file '{frames[-1][0]}'\n")
    ff("-f", "concat", "-safe", "0", "-i", str(work / "audio.txt"), str(work / "voice.wav"))
    ff("-f", "concat", "-safe", "0", "-i", str(work / "video.txt"), "-i", str(work / "voice.wav"),
       "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-crf", "18",
       "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out_path))
    # keep the settled last frame of each slide for checking, drop the rest
    check = out_path.parent / "check"
    shutil.rmtree(check, ignore_errors=True)
    check.mkdir()
    for i in range(len(slides)):
        last_key = max(k for k, si, *_ in items if si == i)
        shutil.copy(work / f"{last_key}.png", check / f"slide-{i + 1:02d}.png")
    shutil.rmtree(work)
    print(f"wrote {out_path} ({sum(d for _, d in frames):.0f}s); last frame of each slide in {check}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = pathlib.Path(sys.argv[1])
    render(src, pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else src.parent / f"{src.resolve().parent.name}.mp4")

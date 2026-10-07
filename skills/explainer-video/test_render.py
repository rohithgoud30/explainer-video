"""Run: uv run --with imageio-ffmpeg --with soundfile --with kokoro-onnx --with edge-tts --with playwright python test_render.py"""
import json
import pathlib
import tempfile

from render import chapters_json, chapters_metadata, inline_images, speakable

assert speakable("Learn HTML and CSS.", {}) == "Learn H-T-M-L and C-S-S."
assert speakable("Two APIs and a URL", {}) == "Two A-P-I's and a U-R-L"
assert speakable("Parse JSON from the DOM", {}) == "Parse JSON from the DOM"        # said as words
assert speakable("No AI today", {"AI": "A-eye"}) == "No A-eye today"                 # pronounce wins
assert speakable("Week A1, the I in API", {}) == "Week A1, the I in A-P-I"           # A1 and single letters untouched
assert speakable("Use Node.js", {"Node.js": "node J-S"}) == "Use node J-S"
# Local slide images are embedded; web URLs and data URIs are left alone.
with tempfile.TemporaryDirectory() as d:
    (pathlib.Path(d) / "shots").mkdir()
    (pathlib.Path(d) / "shots" / "a.png").write_bytes(b"\x89PNG")
    out = inline_images('<img src="shots/a.png"> <img src=https://x.com/b.png> <img src="data:image/png;base64,AA">', pathlib.Path(d))
    assert 'src="data:image/png;base64,iVBORw==' in out, out
    assert "src=https://x.com/b.png" in out and 'src="data:image/png;base64,AA"' in out
    # Code text on a slide that merely mentions src= is not an image.
    code = '<pre>&lt;script src="script.js"&gt;&lt;/script&gt;</pre>'
    assert inline_images(code, pathlib.Path(d)) == code

# One chapter per slide; HTML stripped and FFMETADATA specials escaped.
meta = chapters_metadata(["Intro", "a = b; <b>c</b>"], [0.0, 3.5], 7.25)
assert meta.startswith(";FFMETADATA1\n[CHAPTER]")
assert "START=0\nEND=3500\ntitle=Intro" in meta and "START=3500\nEND=7250\ntitle=a \\= b\\; c" in meta, meta

# The chapters file carries each slide's links; a bare URL becomes {label, url}.
data = json.loads(chapters_json([{"title": "<b>Intro</b>", "links": ["https://a.dev"]},
                                 {"title": "Two", "links": [{"label": "Docs", "url": "https://b.dev#x"}]}], [0.0, 2.5]))
assert data == [{"start": 0.0, "title": "Intro", "links": [{"label": "https://a.dev", "url": "https://a.dev"}]},
                {"start": 2.5, "title": "Two", "links": [{"label": "Docs", "url": "https://b.dev#x"}]}], data

print("ok")

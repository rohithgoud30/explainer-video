"""Run: uv run --with imageio-ffmpeg --with soundfile --with kokoro-onnx --with edge-tts --with playwright python test_render.py"""
import pathlib
import tempfile

from render import inline_images, speakable

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

print("ok")

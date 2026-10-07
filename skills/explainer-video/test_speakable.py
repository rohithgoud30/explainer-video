"""Run: uv run --with imageio-ffmpeg --with soundfile --with kokoro-onnx --with edge-tts --with playwright python test_speakable.py"""
from render import speakable

assert speakable("Learn HTML and CSS.", {}) == "Learn H-T-M-L and C-S-S."
assert speakable("Two APIs and a URL", {}) == "Two A-P-I's and a U-R-L"
assert speakable("Parse JSON from the DOM", {}) == "Parse JSON from the DOM"        # said as words
assert speakable("No AI today", {"AI": "A-eye"}) == "No A-eye today"                 # pronounce wins
assert speakable("Week A1, the I in API", {}) == "Week A1, the I in A-P-I"           # A1 and single letters untouched
assert speakable("Use Node.js", {"Node.js": "node J-S"}) == "Use node J-S"
print("ok")

"""Print every glyph and title the builds draw with Pillow, one line per character.

usage: render_outputs.py <repo root>

The builds need ROMs, which CI does not have, but the pixels they draw come from the fonts in
the repo alone. This calls the same drawing functions the builds call, for every syllable and
jamo rather than only the ones a build happens to need, so a Python or Pillow update that moves
a single pixel shows up as a changed line. The root is an argument so one copy of this script
can render an older tree with that tree's own .venv.

A function that rejects a character (the build would stop on it) prints the error instead,
since a character starting or stopping to fit is also a change.
"""
import hashlib
import importlib
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
CHARS = [chr(c) for c in range(0x3131, 0x3164)] + [chr(c) for c in range(0xAC00, 0xD7A4)]


def tools(game):
    """Import modules from one game's tools/, without another game's same-named modules leaking in."""
    path = str(ROOT / "sfc" / game / "tools")
    for name in [m for m, mod in sys.modules.items() if getattr(mod, "__file__", None)
                 and Path(mod.__file__).is_relative_to(ROOT / "sfc")]:
        del sys.modules[name]
    sys.path[:] = [p for p in sys.path if not p.startswith(str(ROOT / "sfc"))]
    sys.path.insert(0, path)
    return importlib.import_module


def emit(label, fn):
    for ch in CHARS:
        try:
            out = repr(fn(ch))
        except (SystemExit, AssertionError, ValueError) as e:
            out = f"{type(e).__name__}: {e}"
        print(label, ch, hashlib.sha256(out.encode()).hexdigest()[:16])


def title(label, mod, *build):
    s = mod.Screen(bytes(0x4000), bytes(0x800))
    for step in build:
        step(s)
    print(label, hashlib.sha256(repr(sorted(s.px.items())).encode()).hexdigest()[:16])


def kakusei():
    imp = tools("dragon-ball-z-super-gokuden-kakusei")
    from PIL import ImageFont
    dialogue, font16, title_ = imp("dialogue_patch"), imp("font16"), imp("title")
    emit("kakusei.dialogue", dialogue.draw_glyph)
    gfont = ImageFont.truetype(font16.GLYPH_FONT, 12)
    org = font16.origin(gfont)
    emit("kakusei.name", lambda ch: font16.pack(font16.draw(ch, gfont, org)))
    cfont = ImageFont.truetype(font16.CONDENSED_FONT, 12)
    emit("kakusei.condensed", lambda ch: font16.condensed(ch, cfont))
    title("kakusei.title", title_, title_.build_title, lambda s: title_.build_copyright(s, title_.COPYRIGHT))


def totsugeki():
    imp = tools("dragon-ball-z-super-gokuden-totsugeki")
    from PIL import ImageFont
    text, font8, title_ = imp("text_patch1"), imp("font8"), imp("title")
    emit("totsugeki.text", text.draw_glyph)
    font = ImageFont.truetype(font8.FONT, 12)
    emit("totsugeki.name", lambda ch: font8.draw(ch, font))
    title("totsugeki.title", title_, title_.build_title, lambda s: title_.build_copyright(s, title_.COPYRIGHT))


def otogirisou():
    mkfont = tools("otogirisou")("mkfont")
    print("otogirisou.box", mkfont.hangul_box())
    emit("otogirisou.glyph", mkfont.render)


def smrpg():
    build = tools("super-mario-rpg")("build")
    from PIL import ImageFont
    font = ImageFont.truetype(str(build.FONT), 12)
    emit("smrpg.glyph", lambda ch: build.render_glyph(font, ch))


for game in (kakusei, totsugeki, otogirisou, smrpg):
    game()

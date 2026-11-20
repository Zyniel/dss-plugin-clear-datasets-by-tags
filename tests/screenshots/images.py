"""The README images: a screenshot of DSS, with a frame, reduced to a 256-colour palette. See docs/screenshots.md.

Pillow is imported in the functions: without the screenshots dependency group, as in the CI, pytest still imports
the test files of this folder.
"""

import io
from pathlib import Path

from support.dataiku_stub import ROOT

IMAGES = ROOT / "docs" / "images"

# The device scale factor of the screenshots: the README shows them at half their width, sharp on every screen.
SCALE = 2

# A frame of one pixel, at the scale of the screenshots, in the colour of the borders of GitHub: the white dialog
# stands out on the white page of the README. The images taken by hand had the same frame.
FRAME_WIDTH = SCALE
FRAME_COLOUR = (208, 215, 222)


def build_readme_image(screenshot: bytes) -> bytes:
    """Return the README image of a screenshot, as a PNG: framed, and reduced to a palette of 256 colours."""
    from PIL import Image, ImageOps

    image = ImageOps.expand(Image.open(io.BytesIO(screenshot)).convert("RGB"), border=FRAME_WIDTH, fill=FRAME_COLOUR)
    buffer = io.BytesIO()
    image.quantize(colors=256).save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def read_size(png: bytes) -> tuple[int, int]:
    """Return the width and the height of an image, in pixels."""
    from PIL import Image

    with Image.open(io.BytesIO(png)) as image:
        size: tuple[int, int] = image.size
    return size


def write_readme_image(macro_id: str, image_name: str, png: bytes) -> Path:
    """Write a README image of a macro in place of the old one, such as its "form", and return its path."""
    path = IMAGES / macro_id / f"{image_name}.png"
    path.write_bytes(png)
    return path

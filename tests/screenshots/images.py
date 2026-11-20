"""The README images: a screenshot of DSS, with a frame, reduced to a 256-colour palette. See docs/screenshots.md.

Pillow is imported in the functions: without the screenshots dependency group, as in the CI, pytest still imports
the test files of this folder.
"""

import io

from support.dataiku_stub import ROOT

IMAGES = ROOT / "docs" / "images"

# The device scale factor of the screenshots: the README shows them at half their width, sharp on every screen.
SCALE = 2

# A frame of one pixel, at the scale of the screenshots, in the colour of the borders of GitHub: the white dialog
# stands out on the white page of the README. The images taken by hand had the same frame.
FRAME_WIDTH = SCALE
FRAME_COLOUR = (208, 215, 222)

# The edges of a dialog of DSS are white: a darker line inside the frame is the page behind the dialog.
WHITE_ENOUGH = 245


def build_readme_image(screenshot: bytes) -> bytes:
    """Return the README image of a screenshot, as a PNG: framed, and reduced to a palette of 256 colours."""
    from PIL import Image, ImageOps

    image = ImageOps.expand(Image.open(io.BytesIO(screenshot)).convert("RGB"), border=FRAME_WIDTH, fill=FRAME_COLOUR)
    buffer = io.BytesIO()
    image.quantize(colors=256).save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def find_page_edges(png: bytes) -> list[str]:
    """Return the edges of a README image, such as "top", where the line inside the frame is not white.

    Such a line is the page behind the dialog: most of its pixels are dark. A separator of the dialog crosses its
    left and right edges on a few pixels only. The corners are left out: the dialog may round them.
    """
    from PIL import Image

    with Image.open(io.BytesIO(png)) as image:
        rgb = image.convert("RGB")
    width, height = rgb.size
    inner = FRAME_WIDTH
    lines = {
        "top": [(x, inner) for x in range(width // 10, width - width // 10)],
        "bottom": [(x, height - inner - 1) for x in range(width // 10, width - width // 10)],
        "left": [(inner, y) for y in range(height // 10, height - height // 10)],
        "right": [(width - inner - 1, y) for y in range(height // 10, height - height // 10)],
    }
    return [
        edge
        for edge, pixels in lines.items()
        if sum(min(rgb.getpixel(pixel)) < WHITE_ENOUGH for pixel in pixels) > len(pixels) // 2
    ]


def write_readme_images(images: dict[tuple[str, str], bytes]) -> None:
    """Write README images in place of the old ones, once all of them are built.

    :param images: each PNG by the id of its macro and its name, such as ("report-dataset-tags", "form")
    """
    for (macro_id, image_name), png in images.items():
        (IMAGES / macro_id / f"{image_name}.png").write_bytes(png)

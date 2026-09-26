r"""
High-quality, reasonable-size PDF.
No downsampling. JPEG quality 90, no chroma subsampling.
Result: ~1 MB per page for typical newspaper scans.

Project: Eenadu E-Paper PDF Pipeline
Usage  : python make_pdf_hq.py <image_folder> <output_pdf>

Example:
    python make_pdf_hq.py pages_shot "Eenadu 17-09-2026 Telangana.pdf"
"""

import os
import sys
from PIL import Image

# --- Config ---
A4_W_IN = 8.27
A4_H_IN = 11.69
DPI     = 200
QUALITY = 90


def make_pdf(folder, output):
    valid = ('.png', '.jpg', '.jpeg')
    files = sorted([
        os.path.join(folder, f) for f in os.listdir(folder)
        if f.lower().endswith(valid)
    ])

    if not files:
        print(f"No images in {folder}")
        return

    A4_W = int(A4_W_IN * DPI)
    A4_H = int(A4_H_IN * DPI)

    print("Eenadu PDF Builder")
    print(f"Building PDF — quality {QUALITY}, no downsampling")
    print(f"Pages: {len(files)}\n")

    pages = []

    for i, f in enumerate(files, 1):
        img = Image.open(f).convert("RGB")

        # A4 canvas is large enough to fit the image at native pixels
        canvas_w = max(A4_W, img.width)
        canvas_h = max(A4_H, img.height)

        canvas = Image.new("RGB", (canvas_w, canvas_h), "white")

        x = (canvas_w - img.width) // 2
        y = (canvas_h - img.height) // 2

        canvas.paste(img, (x, y))
        pages.append(canvas)

        print(f"  [{i:02d}/{len(files)}] {os.path.basename(f)}: {img.size}")

    # Save PDF
    pages[0].save(
        output,
        save_all=True,
        append_images=pages[1:],
        dpi=(DPI, DPI),
        quality=QUALITY,
        subsampling=0,
        optimize=True,
        progressive=True,
        title=os.path.basename(output),
        creator="Eenadu",
    )

    mb = os.path.getsize(output) / (1024 * 1024)

    print(f"\nPDF: {output}")
    print("Creator: Eenadu")
    print(f"Size: {mb:.1f} MB  ({mb * 1024 / len(files):.0f} KB/page)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    make_pdf(sys.argv[1], sys.argv[2])
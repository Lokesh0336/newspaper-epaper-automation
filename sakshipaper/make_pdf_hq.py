# ============================================================
# Newspaper E-Paper Automation
# Open Source Project
# Copyright (c) 2026
#
# Licensed under the MIT License.
# See LICENSE file for details.
# ============================================================
import os
from datetime import datetime
from PIL import Image


# ---------- CONFIG ----------

SRC = r"C:\newspaper\sakshipaper\pages_shot"

OUT_DIR = r"C:\newspaper\sakshipaper"

EDITION = "Telangana"

DATE_STR = None
# None = today's date (DD-MM-YYYY)
# Example: DATE_STR = "26-09-2026"


# ---------------------------------------------


def build_filename(edition, date_str=None):

    if date_str is None:
        date_str = datetime.now().strftime("%d-%m-%Y")

    return f"Sakshi {date_str} {edition}.pdf"


def main():

    files = sorted(
        f
        for f in os.listdir(SRC)
        if f.lower().endswith(
            (".jpg", ".jpeg", ".png")
        )
    )

    if not files:
        print("No images in", SRC)
        return

    print(f"Found {len(files)} pages")

    imgs = []

    for f in files:

        img = Image.open(
            os.path.join(SRC, f)
        ).convert("RGB")

        imgs.append(img)

        print(
            f"Loaded {f}: "
            f"{img.width} x {img.height}"
        )


    # Normalize all pages to the first page's size

    W, H = imgs[0].size

    imgs = [
        im
        if im.size == (W, H)
        else im.resize(
            (W, H),
            Image.LANCZOS
        )
        for im in imgs
    ]


    # Build output path

    fname = build_filename(
        EDITION,
        DATE_STR
    )

    out_path = os.path.join(
        OUT_DIR,
        fname
    )

    title = fname[:-4]


    # Save PDF

    first = imgs[0]
    rest = imgs[1:]

    first.save(
        out_path,
        "PDF",
        resolution=200.0,
        save_all=True,
        append_images=rest,
        quality=90,
        subsampling=0,
        optimize=True,
        progressive=True,
        title=title,
        creator="Sakshi",
        subject=EDITION,
    )


    size_mb = (
        os.path.getsize(out_path)
        / 1024
        / 1024
    )


    print(
        f"\n[OK] PDF: {out_path} "
        f"({size_mb:.1f} MB)"
    )


if __name__ == "__main__":
    main()
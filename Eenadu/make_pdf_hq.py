# ============================================================
# Newspaper E-Paper Automation
# Open Source Project
# Copyright (c) 2026
#
# Licensed under the MIT License.
# See LICENSE file for details.
# ============================================================
"""
Eenadu High Quality PDF Builder

Usage:

Normal:
    python make_pdf_hq.py pages_shot "Eenadu 27-09-2026 Telangana.pdf"

District edition:
    python make_pdf_hq.py Edition_shots\\27-09-2026\\JAGTIAL "Eenadu 27-09-2026 Jagtial.pdf"
"""

import os
import sys

from PIL import Image


# ============================================================
# PDF SETTINGS
# ============================================================

DPI = 200

QUALITY = 90


# ============================================================
# BUILD PDF
# ============================================================

def make_pdf(
    folder,
    output
):

    if not os.path.isdir(
        folder
    ):

        print(
            f"[ERROR] Folder does not exist:"
        )

        print(
            folder
        )

        return


    valid_extensions = (
        ".png",
        ".jpg",
        ".jpeg",
    )


    files = sorted(
        [
            os.path.join(
                folder,
                filename
            )
            for filename in os.listdir(
                folder
            )
            if filename.lower().endswith(
                valid_extensions
            )
        ]
    )


    if not files:

        print(
            f"[ERROR] No images found in:"
        )

        print(
            folder
        )

        return


    print()
    print("=" * 65)
    print("EENADU PDF BUILDER")
    print("=" * 65)

    print(
        f"Folder : {folder}"
    )

    print(
        f"Pages  : {len(files)}"
    )

    print(
        f"DPI    : {DPI}"
    )

    print(
        f"Quality: {QUALITY}"
    )

    print("=" * 65)


    pages = []


    for index, filepath in enumerate(
        files,
        start=1
    ):

        print(
            f"[{index:03d}/{len(files):03d}] "
            f"{os.path.basename(filepath)}"
        )


        try:

            image = Image.open(
                filepath
            ).convert(
                "RGB"
            )


            pages.append(
                image
            )


        except Exception as error:

            print(
                f"    [ERROR] {error}"
            )


    if not pages:

        print(
            "\n[ERROR] No valid images."
        )

        return


    # --------------------------------------------------------
    # Ensure output directory exists.
    # --------------------------------------------------------

    output_directory = os.path.dirname(
        os.path.abspath(
            output
        )
    )


    os.makedirs(
        output_directory,
        exist_ok=True
    )


    # --------------------------------------------------------
    # Save PDF
    # --------------------------------------------------------

    first = pages[0]

    remaining = pages[1:]


    first.save(
        output,
        "PDF",
        resolution=float(DPI),
        save_all=True,
        append_images=remaining,
        quality=QUALITY,
        subsampling=0,
        optimize=True,
        progressive=True,
        title=os.path.basename(
            output
        ),
        creator="Eenadu",
        subject="Eenadu E-Paper",
    )


    size_mb = (
        os.path.getsize(
            output
        )
        / (1024 * 1024)
    )


    print()
    print("=" * 65)
    print("PDF CREATED")
    print("=" * 65)

    print(
        f"PDF   : {output}"
    )

    print(
        f"Pages : {len(pages)}"
    )

    print(
        f"Size  : {size_mb:.1f} MB"
    )

    print("=" * 65)


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) < 3:

        print(
            __doc__
        )

        sys.exit(1)


    folder = sys.argv[1]

    output = sys.argv[2]


    make_pdf(
        folder,
        output
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
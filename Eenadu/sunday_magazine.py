# ============================================================
# Eenadu E-Paper - Sunday Magazine Downloader
# ============================================================
#
# Features:
#   - Open first Sunday Magazine page only
#   - Automatically navigate through all pages
#   - No manual PID list
#   - No manual page count
#   - Capture only the actual newspaper/magazine page
#   - Automatically create A4 PDF
#   - Automatically delete PNG screenshots after
#     successful PDF creation
#   - If PDF creation fails, screenshots are preserved
#
# Usage:
#
#   python sunday_magazine.py 27/09/2026
#
# ============================================================

import os
import re
import sys
import time
import base64

import undetected_chromedriver as uc

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from PIL import Image
from io import BytesIO


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = r"C:\newspaper\Eenadu"

OUTPUT_BASE_DIR = os.path.join(
    BASE_DIR,
    "Edition_shots"
)

PROFILE_DIR = r"C:\newspaper\chrome_profile"

# Sunday Magazine EID
EID = 367

# ONLY THE FIRST PID IS REQUIRED.
# The script discovers the remaining pages automatically.
FIRST_PID = 3597735

SCALE = 2

WAIT_AFTER_INITIAL_LOAD = 25

WAIT_AFTER_TURN = 3

WAIT_FOR_TURN_TIMEOUT = 15

MAX_PAGES = 100

CROP_TOP_PX = 0


# ============================================================
# BUILD URL
# ============================================================

def build_url(date_string, pid):

    return (
        "https://epaper.eenadu.net/Home/Index"
        f"?date={date_string}"
        f"&eid={EID}"
        f"&pid={pid}"
    )


# ============================================================
# BUILD DRIVER
# ============================================================

def build_driver():

    options = uc.ChromeOptions()

    options.add_argument(
        "--window-size=1800,2400"
    )

    options.add_argument(
        "--force-device-scale-factor=1"
    )

    if os.path.isdir(PROFILE_DIR):

        options.add_argument(
            f"--user-data-dir={PROFILE_DIR}"
        )

        options.add_argument(
            "--profile-directory=Default"
        )

        print(
            f"[i] Using profile: {PROFILE_DIR}"
        )

    return uc.Chrome(
        options=options,
        headless=False,
        use_subprocess=True
    )


# ============================================================
# FIND MAGAZINE IMAGE
# ============================================================

def find_page_element(driver):

    # IMPORTANT:
    #
    # For Sunday Magazine, prioritize imgmain1.
    #
    # This prevents capturing the surrounding viewer/list
    # instead of the actual magazine page.

    selectors = [
        ("id", "imgmain1"),
        ("id", "ImageContainer"),
        ("id", "homeMainImgBox"),
    ]

    for selector_type, selector_value in selectors:

        try:

            element = driver.find_element(
                By.ID,
                selector_value
            )

            width = element.size["width"]
            height = element.size["height"]

            if (
                width > 400
                and height > 400
            ):

                return element, selector_value

        except Exception:

            pass

    return None, None


# ============================================================
# GET IMAGE SRC
# ============================================================

def get_image_src(driver):

    try:

        return driver.find_element(
            By.ID,
            "imgmain1"
        ).get_attribute(
            "src"
        ) or ""

    except Exception:

        return ""


# ============================================================
# GET CURRENT PID
# ============================================================

def get_current_pid(driver):

    try:

        url = driver.current_url

        match = re.search(
            r"[?&]pid=(\d+)",
            url
        )

        if match:

            return match.group(1)

    except Exception:

        pass

    return ""


# ============================================================
# GET PAGE NUMBER FROM IMAGE
# ============================================================

def page_number_from_src(src):

    if not src:

        return None

    patterns = [

        r'_(\d{2})_hr\.(?:jpg|png)',

        r'_(\d+)_hr\.(?:jpg|png)',

        r'_(\d+)\.(?:jpg|png)',

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            src,
            re.IGNORECASE
        )

        if match:

            try:

                return int(
                    match.group(1)
                )

            except Exception:

                pass

    return None


# ============================================================
# GET PAGE SIGNATURE
# ============================================================

def get_page_signature(driver):

    src = get_image_src(
        driver
    )

    pid = get_current_pid(
        driver
    )

    page_number = page_number_from_src(
        src
    )

    return (
        src,
        pid,
        page_number
    )


# ============================================================
# WAIT FOR IMAGE READY
# ============================================================

def wait_for_page_ready(
    driver,
    timeout=20
):

    end_time = (
        time.time()
        + timeout
    )

    while time.time() < end_time:

        try:

            state = driver.execute_script(
                """
                const img =
                    document.querySelector('#imgmain1');

                if (!img)
                    return 'no-img';

                if (!img.complete)
                    return 'loading';

                if (img.naturalWidth < 100)
                    return 'tiny';

                if (img.naturalHeight < 100)
                    return 'tiny';

                return 'ready';
                """
            )

            if state == "ready":

                return True

        except Exception:

            pass

        time.sleep(
            0.4
        )

    return False


# ============================================================
# WAIT FOR PAGE CHANGE
# ============================================================

def wait_for_page_change(
    driver,
    old_signature,
    timeout=WAIT_FOR_TURN_TIMEOUT
):

    end_time = (
        time.time()
        + timeout
    )

    while time.time() < end_time:

        try:

            new_signature = get_page_signature(
                driver
            )

            old_src, old_pid, old_page = (
                old_signature
            )

            new_src, new_pid, new_page = (
                new_signature
            )

            src_changed = (
                bool(new_src)
                and
                new_src != old_src
            )

            pid_changed = (
                bool(new_pid)
                and
                new_pid != old_pid
            )

            page_changed = (
                new_page is not None
                and
                old_page is not None
                and
                new_page != old_page
            )

            if (
                src_changed
                or pid_changed
                or page_changed
            ):

                if wait_for_page_ready(
                    driver,
                    timeout=10
                ):

                    return True

        except Exception:

            pass

        time.sleep(
            0.4
        )

    return False


# ============================================================
# HIDE STICKY ELEMENTS
# ============================================================

def hide_sticky_overlays(driver):

    try:

        driver.execute_script(
            """
            window.__hidden_stack = [];

            document.querySelectorAll('*').forEach(el => {

                try {

                    const s =
                        window.getComputedStyle(el);

                    if (
                        s.position === 'fixed'
                        ||
                        s.position === 'sticky'
                    ) {

                        window.__hidden_stack.push([
                            el,
                            el.style.visibility
                        ]);

                        el.style.visibility =
                            'hidden';
                    }

                } catch(e) {}

            });
            """
        )

        time.sleep(
            0.2
        )

    except Exception:

        pass


# ============================================================
# RESTORE STICKY ELEMENTS
# ============================================================

def restore_overlays(driver):

    try:

        driver.execute_script(
            """
            (window.__hidden_stack || [])
                .forEach(([el, visibility]) => {

                    try {

                        el.style.visibility =
                            visibility;

                    } catch(e) {}

                });

            window.__hidden_stack = [];
            """
        )

    except Exception:

        pass


# ============================================================
# CAPTURE EXACT MAGAZINE PAGE
# ============================================================

def capture(
    driver,
    element,
    output_path,
    scale=SCALE,
    crop_top=CROP_TOP_PX
):

    # --------------------------------------------------------
    # Scroll the actual magazine image to the top.
    # --------------------------------------------------------

    driver.execute_script(
        """
        arguments[0].scrollIntoView({
            block: 'start',
            inline: 'center'
        });
        """,
        element
    )

    time.sleep(
        0.3
    )


    # --------------------------------------------------------
    # Hide viewer overlays.
    # --------------------------------------------------------

    hide_sticky_overlays(
        driver
    )

    try:

        # ----------------------------------------------------
        # Get exact magazine image rectangle.
        # ----------------------------------------------------

        rect = driver.execute_script(
            """
            const r =
                arguments[0].getBoundingClientRect();

            return {
                x:
                    r.left + window.scrollX,

                y:
                    r.top + window.scrollY,

                w:
                    r.width,

                h:
                    r.height
            };
            """,
            element
        )


        # ----------------------------------------------------
        # Capture ONLY that element.
        # ----------------------------------------------------

        result = driver.execute_cdp_cmd(
            "Page.captureScreenshot",
            {
                "format": "png",

                "captureBeyondViewport": True,

                "clip": {
                    "x": rect["x"],
                    "y": rect["y"],
                    "width": rect["w"],
                    "height": rect["h"],
                    "scale": scale
                }
            }
        )


        png_bytes = base64.b64decode(
            result["data"]
        )

    finally:

        restore_overlays(
            driver
        )


    # --------------------------------------------------------
    # Optional crop.
    # --------------------------------------------------------

    if crop_top > 0:

        image = Image.open(
            BytesIO(
                png_bytes
            )
        )

        width, height = image.size

        image = image.crop(
            (
                0,
                crop_top,
                width,
                height
            )
        )

        image.save(
            output_path
        )

    else:

        with open(
            output_path,
            "wb"
        ) as f:

            f.write(
                png_bytes
            )


# ============================================================
# ARROW RIGHT
# ============================================================

def try_arrow_right(driver):

    try:

        body = driver.find_element(
            By.TAG_NAME,
            "body"
        )

        body.send_keys(
            Keys.ARROW_RIGHT
        )

        return True

    except Exception:

        return False


# ============================================================
# NEXT BUTTON
# ============================================================

def try_next_button(driver):

    try:

        elements = driver.find_elements(
            By.XPATH,

            "//*[contains(@id,'next') "
            "or contains(@class,'next') "
            "or contains(@src,'right') "
            "or contains(@alt,'next') "
            "or contains(@onclick,'next')]"
        )

        for element in elements:

            try:

                if not element.is_displayed():

                    continue

                width = element.size["width"]
                height = element.size["height"]

                if (
                    width < 10
                    or height < 10
                ):

                    continue

                driver.execute_script(
                    "arguments[0].click();",
                    element
                )

                return True

            except Exception:

                continue

    except Exception:

        pass

    return False


# ============================================================
# TURN TO NEXT PAGE
# ============================================================

def turn_to_next_page(
    driver,
    old_signature
):

    # --------------------------------------------------------
    # ArrowRight
    # --------------------------------------------------------

    print(
        "        Trying ArrowRight..."
    )

    if try_arrow_right(
        driver
    ):

        time.sleep(
            WAIT_AFTER_TURN
        )

        if wait_for_page_change(
            driver,
            old_signature
        ):

            return "arrow-key"


    print(
        "        ArrowRight did not change page."
    )


    # --------------------------------------------------------
    # Next button
    # --------------------------------------------------------

    print(
        "        Trying next button..."
    )

    if try_next_button(
        driver
    ):

        time.sleep(
            WAIT_AFTER_TURN
        )

        if wait_for_page_change(
            driver,
            old_signature
        ):

            return "next-button"


    # --------------------------------------------------------
    # No next page.
    # --------------------------------------------------------

    print(
        "        No next page detected."
    )

    print(
        "        Current page is the last page."
    )

    return None


# ============================================================
# CREATE A4 PDF
# ============================================================

def create_a4_pdf(
    output_dir,
    date_str,
    captured_pages
):

    """
    Creates an A4 300-DPI PDF.

    PNG files are deleted ONLY after:
        1. PDF creation succeeds
        2. PDF exists
        3. PDF size > 0
    """

    if captured_pages <= 0:

        print(
            "[!] No captured pages."
        )

        return None


    # --------------------------------------------------------
    # A4 at 300 DPI
    # --------------------------------------------------------

    A4_WIDTH = 2480
    A4_HEIGHT = 3508

    MARGIN = 60

    MAX_WIDTH = (
        A4_WIDTH
        - (MARGIN * 2)
    )

    MAX_HEIGHT = (
        A4_HEIGHT
        - (MARGIN * 2)
    )


    # --------------------------------------------------------
    # Find PNG screenshots.
    # --------------------------------------------------------

    image_files = []

    for page_number in range(
        1,
        captured_pages + 1
    ):

        path = os.path.join(
            output_dir,
            f"page_{page_number:03d}.png"
        )

        if os.path.isfile(
            path
        ):

            image_files.append(
                path
            )


    if not image_files:

        print(
            "[!] No screenshots found."
        )

        return None


    # --------------------------------------------------------
    # PDF filename.
    # --------------------------------------------------------

    safe_date = (
        date_str.replace(
            "/",
            "-"
        )
    )

    pdf_path = os.path.join(
        output_dir,
        f"Eenadu {safe_date} Sunday Magazine A4.pdf"
    )


    print()

    print(
        "=" * 70
    )

    print(
        "CREATING A4 PDF"
    )

    print(
        "=" * 70
    )

    print(
        f"Pages : {len(image_files)}"
    )

    print(
        f"PDF   : {pdf_path}"
    )

    print()


    pdf_pages = []


    # --------------------------------------------------------
    # Convert each screenshot to an A4 page.
    # --------------------------------------------------------

    for index, image_path in enumerate(
        image_files,
        start=1
    ):

        try:

            image = Image.open(
                image_path
            ).convert(
                "RGB"
            )

            original_width, original_height = (
                image.size
            )


            # ------------------------------------------------
            # Preserve aspect ratio.
            # ------------------------------------------------

            scale_x = (
                MAX_WIDTH
                / original_width
            )

            scale_y = (
                MAX_HEIGHT
                / original_height
            )

            scale = min(
                scale_x,
                scale_y
            )


            new_width = max(
                1,
                int(
                    original_width
                    * scale
                )
            )

            new_height = max(
                1,
                int(
                    original_height
                    * scale
                )
            )


            resized = image.resize(
                (
                    new_width,
                    new_height
                ),
                Image.Resampling.LANCZOS
            )


            # ------------------------------------------------
            # White A4 canvas.
            # ------------------------------------------------

            page = Image.new(
                "RGB",
                (
                    A4_WIDTH,
                    A4_HEIGHT
                ),
                "white"
            )


            # ------------------------------------------------
            # Center page.
            # ------------------------------------------------

            x = (
                A4_WIDTH
                - new_width
            ) // 2

            y = (
                A4_HEIGHT
                - new_height
            ) // 2


            page.paste(
                resized,
                (
                    x,
                    y
                )
            )


            pdf_pages.append(
                page
            )


            print(
                f"  [{index:03d}/"
                f"{len(image_files):03d}] "
                f"{os.path.basename(image_path)}"
            )


        except Exception as e:

            print(
                f"[!] Failed to process "
                f"{image_path}"
            )

            print(
                f"    {e}"
            )


    # --------------------------------------------------------
    # Nothing to save.
    # --------------------------------------------------------

    if not pdf_pages:

        print(
            "[!] PDF pages could not be generated."
        )

        print(
            "[!] Screenshots will NOT be deleted."
        )

        return None


    # --------------------------------------------------------
    # SAVE PDF
    # --------------------------------------------------------

    try:

        pdf_pages[0].save(
            pdf_path,
            "PDF",
            resolution=300.0,
            save_all=True,
            append_images=pdf_pages[1:],
            title=(
                f"Eenadu "
                f"{safe_date} "
                f"Sunday Magazine"
            ),
            creator="Eenadu"
        )

    except Exception as e:

        print()

        print(
            "[ERROR] PDF creation failed."
        )

        print(
            f"        {e}"
        )

        print()

        print(
            "[IMPORTANT] Screenshots were NOT deleted."
        )

        return None


    # ========================================================
    # VERIFY PDF
    # ========================================================

    if not os.path.isfile(
        pdf_path
    ):

        print()

        print(
            "[ERROR] PDF file does not exist "
            "after creation."
        )

        print(
            "[IMPORTANT] Screenshots were NOT deleted."
        )

        return None


    pdf_size = os.path.getsize(
        pdf_path
    )


    if pdf_size <= 0:

        print()

        print(
            "[ERROR] PDF file is empty."
        )

        print(
            "[IMPORTANT] Screenshots were NOT deleted."
        )

        return None


    # ========================================================
    # PDF SUCCESS
    # ========================================================

    print()

    print(
        "[OK] A4 PDF created successfully."
    )

    print(
        f"[OK] PDF: {pdf_path}"
    )

    print(
        f"[OK] Size: "
        f"{pdf_size / (1024 * 1024):.2f} MB"
    )


    # ========================================================
    # DELETE SCREENSHOTS
    # ========================================================

    print()

    print(
        "=" * 70
    )

    print(
        "DELETING SCREENSHOTS"
    )

    print(
        "=" * 70
    )


    deleted_count = 0

    failed_count = 0


    for image_path in image_files:

        try:

            if os.path.isfile(
                image_path
            ):

                os.remove(
                    image_path
                )

                deleted_count += 1

                print(
                    f"[DELETED] "
                    f"{os.path.basename(image_path)}"
                )

        except Exception as e:

            failed_count += 1

            print(
                f"[WARNING] Could not delete "
                f"{os.path.basename(image_path)}"
            )

            print(
                f"          {e}"
            )


    # ========================================================
    # CLEANUP SUMMARY
    # ========================================================

    print()

    print(
        f"[OK] Screenshots deleted: "
        f"{deleted_count}"
    )

    if failed_count == 0:

        print(
            "[OK] All screenshots deleted successfully."
        )

    else:

        print(
            f"[WARNING] "
            f"{failed_count} screenshot(s) "
            "could not be deleted."
        )


    return pdf_path


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    if len(sys.argv) < 2:

        print(
            "Usage:"
        )

        print(
            "python sunday_magazine.py DD/MM/YYYY"
        )

        print()

        print(
            "Example:"
        )

        print(
            "python sunday_magazine.py 27/09/2026"
        )

        sys.exit(1)


    date_str = sys.argv[1]


    # --------------------------------------------------------
    # Validate date.
    # --------------------------------------------------------

    if not re.fullmatch(
        r"\d{2}/\d{2}/\d{4}",
        date_str
    ):

        print(
            "[!] Date must be in DD/MM/YYYY format."
        )

        sys.exit(1)


    # --------------------------------------------------------
    # Output folder.
    # --------------------------------------------------------

    safe_date = (
        date_str.replace(
            "/",
            "-"
        )
    )

    output_dir = os.path.join(
        OUTPUT_BASE_DIR,
        safe_date,
        "SUNDAY_MAGAZINE"
    )


    os.makedirs(
        output_dir,
        exist_ok=True
    )


    # --------------------------------------------------------
    # First page URL.
    # --------------------------------------------------------

    url = build_url(
        date_str,
        FIRST_PID
    )


    # --------------------------------------------------------
    # Display.
    # --------------------------------------------------------

    print()

    print(
        "=" * 70
    )

    print(
        "EENADU SUNDAY MAGAZINE DOWNLOADER"
    )

    print(
        "=" * 70
    )

    print(
        f"Date       : {date_str}"
    )

    print(
        f"EID        : {EID}"
    )

    print(
        f"First PID  : {FIRST_PID}"
    )

    print(
        f"Output     : {output_dir}"
    )

    print(
        f"URL        : {url}"
    )

    print(
        "=" * 70
    )


    # --------------------------------------------------------
    # Browser.
    # --------------------------------------------------------

    driver = build_driver()


    try:

        # ----------------------------------------------------
        # Open first page.
        # ----------------------------------------------------

        print()

        print(
            f"Opening: {url}"
        )

        driver.get(
            url
        )


        # ----------------------------------------------------
        # Wait.
        # ----------------------------------------------------

        print()

        print(
            f"[i] Waiting "
            f"{WAIT_AFTER_INITIAL_LOAD}s "
            "for the magazine viewer..."
        )

        time.sleep(
            WAIT_AFTER_INITIAL_LOAD
        )


        # ----------------------------------------------------
        # Find page.
        # ----------------------------------------------------

        element, detected_id = find_page_element(
            driver
        )


        if not element:

            print()

            print(
                "[ERROR] Magazine page was not found."
            )

            print(
                f"[i] Current URL: "
                f"{driver.current_url}"
            )

            return


        print()

        print(
            f"[i] Magazine page detected via "
            f"#{detected_id}."
        )


        # ----------------------------------------------------
        # Wait for first image.
        # ----------------------------------------------------

        if not wait_for_page_ready(
            driver,
            timeout=20
        ):

            print(
                "[ERROR] First magazine page "
                "did not become ready."
            )

            return


        # ----------------------------------------------------
        # Start.
        # ----------------------------------------------------

        print()

        print(
            "[i] Page navigation is automatic."
        )

        print(
            "[i] Page count is automatic."
        )

        print()


        input(
            ">>> Press Enter to begin capture "
            "(zoom viewer to 100% first)... "
        )


        # ----------------------------------------------------
        # Capture loop.
        # ----------------------------------------------------

        captured = 0

        seen_pages = set()


        for page_number in range(
            1,
            MAX_PAGES + 1
        ):

            print()

            print(
                "-" * 70
            )

            print(
                f"PAGE {page_number}"
            )

            print(
                "-" * 70
            )


            # ------------------------------------------------
            # Find actual magazine image.
            # ------------------------------------------------

            element, detected_id = find_page_element(
                driver
            )


            if not element:

                print(
                    "[ERROR] Magazine page "
                    "element disappeared."
                )

                break


            # ------------------------------------------------
            # Wait until loaded.
            # ------------------------------------------------

            if not wait_for_page_ready(
                driver,
                timeout=20
            ):

                print(
                    "[ERROR] Magazine page "
                    "did not become ready."
                )

                break


            # ------------------------------------------------
            # Signature.
            # ------------------------------------------------

            current_signature = (
                get_page_signature(
                    driver
                )
            )


            current_pid = (
                current_signature[1]
            )

            current_page_number = (
                current_signature[2]
            )


            # ------------------------------------------------
            # Duplicate protection.
            # ------------------------------------------------

            if current_signature in seen_pages:

                print(
                    "[!] Duplicate page detected."
                )

                print(
                    "[!] Stopping navigation."
                )

                break


            seen_pages.add(
                current_signature
            )


            # ------------------------------------------------
            # Screenshot path.
            # ------------------------------------------------

            output_path = os.path.join(
                output_dir,
                f"page_{page_number:03d}.png"
            )


            # ------------------------------------------------
            # Capture.
            # ------------------------------------------------

            try:

                capture(
                    driver,
                    element,
                    output_path
                )

            except Exception as e:

                print(
                    "[ERROR] Capture failed:"
                )

                print(
                    f"        {e}"
                )

                break


            captured += 1


            print(
                f"[OK] Page "
                f"{page_number:03d}"
            )

            print(
                f"     PID: "
                f"{current_pid or 'unknown'}"
            )


            if current_page_number is not None:

                print(
                    f"     Viewer page: "
                    f"{current_page_number}"
                )


            print(
                "     Saved:"
            )

            print(
                f"     {output_path}"
            )


            # ------------------------------------------------
            # Next page.
            # ------------------------------------------------

            print()

            print(
                "[i] Turning to next page..."
            )


            method = turn_to_next_page(
                driver,
                current_signature
            )


            # ------------------------------------------------
            # Last page.
            # ------------------------------------------------

            if not method:

                break


            print(
                f"[OK] Page changed using: "
                f"{method}"
            )


        # ----------------------------------------------------
        # Capture finished.
        # ----------------------------------------------------

        print()

        print(
            "=" * 70
        )

        print(
            "CAPTURE FINISHED"
        )

        print(
            "=" * 70
        )

        print(
            f"Pages captured : {captured}"
        )

        print(
            f"Output folder  : {output_dir}"
        )

        print(
            "=" * 70
        )


        # ----------------------------------------------------
        # Create PDF.
        # ----------------------------------------------------

        if captured > 0:

            pdf_path = create_a4_pdf(
                output_dir,
                date_str,
                captured
            )


            if pdf_path:

                print()

                print(
                    "=" * 70
                )

                print(
                    "ALL DONE"
                )

                print(
                    "=" * 70
                )

                print(
                    f"PDF:"
                )

                print(
                    pdf_path
                )

                print()

                print(
                    "PNG screenshots:"
                )

                print(
                    "Deleted automatically"
                )

                print(
                    "=" * 70
                )

            else:

                print()

                print(
                    "=" * 70
                )

                print(
                    "PDF CREATION FAILED"
                )

                print(
                    "=" * 70
                )

                print(
                    "The PNG screenshots have been "
                    "kept for safety."
                )

        else:

            print()

            print(
                "[!] No pages were captured."
            )

            print(
                "[!] PDF was not created."
            )

            print(
                "[!] Screenshots were not deleted."
            )


    finally:

        input(
            "\n>>> Press Enter to close the browser... "
        )

        try:

            driver.quit()

        except Exception:

            pass


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
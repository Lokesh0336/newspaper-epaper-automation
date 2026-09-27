# ============================================================
# Newspaper E-Paper Automation
# Open Source Project
# Copyright (c) 2026
#
# Licensed under the MIT License.
# See LICENSE file for details.
# ============================================================
"""
Eenadu E-Paper Edition Downloader

Usage:

    python editions.py DD/MM/YYYY

Example:

    python editions.py 27/09/2026

The script:
1. Shows all available Eenadu editions.
2. Lets the user select an edition.
3. Builds the correct Eenadu URL using EID + PID.
4. Automatically detects the available page count.
5. Captures all pages.
6. Saves screenshots under:

    Edition_shots/
        DD-MM-YYYY/
            EDITION_NAME/
                page_001.png
                page_002.png
                ...
"""

import os
import re
import sys
import time
import base64
from io import BytesIO

import undetected_chromedriver as uc

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from PIL import Image


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = r"C:\newspaper\Eenadu"

PROFILE_DIR = os.path.join(
    BASE_DIR,
    "chrome_profile"
)

EDITION_OUTPUT_BASE = os.path.join(
    BASE_DIR,
    "Edition_shots"
)

SCALE = 2

WAIT_AFTER_INITIAL_LOAD = 25
WAIT_AFTER_TURN = 3
WAIT_FOR_TURN_TIMEOUT = 15

CROP_TOP_PX = 0

MAX_PAGES = 100


# ============================================================
# EENADU EDITIONS
# ============================================================

EDITIONS = {
    "ADILABAD": {
        "eid": 25,
        "pid": 3598125,
    },

    "BHADRADRI KOTHAGUDEM": {
        "eid": 26,
        "pid": 3598000,
    },

    "CYBERABAD": {
        "eid": 239,
        "pid": 3598059,
    },

    "HANUMAKONDA": {
        "eid": 51,
        "pid": 3598138,
    },

    "HYDERABAD": {
        "eid": 27,
        "pid": 3598101,
    },

    "JAGTIAL": {
        "eid": 28,
        "pid": 3598150,
    },

    "JANGAON": {
        "eid": 29,
        "pid": 3598163,
    },

    "JAYASHANKAR BHUPALPALLY": {
        "eid": 30,
        "pid": 3598317,
    },

    "JOGULAMBA GADWAL": {
        "eid": 31,
        "pid": 3598048,
    },

    "KAMAREDDY": {
        "eid": 32,
        "pid": 3598289,
    },

    "KARIMNAGAR": {
        "eid": 33,
        "pid": 3598202,
    },

    "KHAMMAM": {
        "eid": 34,
        "pid": 3598188,
    },

    "KUMURAM BHEEM": {
        "eid": 35,
        "pid": 3598175,
    },

    "MAHABUBABAD": {
        "eid": 36,
        "pid": 3598253,
    },

    "MAHBUBNAGAR": {
        "eid": 37,
        "pid": 3598351,
    },

    "MANCHERIAL": {
        "eid": 38,
        "pid": 3598211,
    },

    "MEDAK": {
        "eid": 39,
        "pid": 3597885,
    },

    "MULUGU": {
        "eid": 275,
        "pid": 3597964,
    },

    "NAGARKURNOOL": {
        "eid": 40,
        "pid": 3598652,
    },

    "NALGONDA": {
        "eid": 41,
        "pid": 3598012,
    },

    "NARAYANPET": {
        "eid": 301,
        "pid": 3598050,
    },

    "NIRMAL": {
        "eid": 42,
        "pid": 3598224,
    },

    "NIZAMABAD": {
        "eid": 43,
        "pid": 3598277,
    },

    "PEDDAPALLE": {
        "eid": 44,
        "pid": 3598234,
    },

    "RAJANNA SIRCILLA": {
        "eid": 45,
        "pid": 3598243,
    },

    "SANGAREDDY": {
        "eid": 46,
        "pid": 3597973,
    },

    "SECUNDERABAD": {
        "eid": 238,
        "pid": 3598164,
    },

    "SIDDIPET": {
        "eid": 47,
        "pid": 3597984,
    },

    "SURYAPET": {
        "eid": 48,
        "pid": 3598025,
    },

    "VIKARABAD": {
        "eid": 49,
        "pid": 3597918,
    },

    "WANAPARTHY": {
        "eid": 50,
        "pid": 3598385,
    },

    "WARANGAL": {
        "eid": 52,
        "pid": 3597941,
    },

    "YADADRI BHUVANAGIRI": {
        "eid": 53,
        "pid": 3598039,
    },

    # Other state editions

    "KARNATAKA": {
        "eid": 13,
        "pid": 3597919,
    },

    "ODISHA": {
        "eid": 17,
        "pid": 3598998,
    },

    "TAMILNADU": {
        "eid": 20,
        "pid": 3597730,
    },
}


# ============================================================
# DATE VALIDATION
# ============================================================

def validate_date(date_str):

    pattern = r"^\d{2}/\d{2}/\d{4}$"

    if not re.match(pattern, date_str):
        return False

    day, month, year = map(int, date_str.split("/"))

    if month < 1 or month > 12:
        return False

    if day < 1 or day > 31:
        return False

    if year < 2000 or year > 2100:
        return False

    return True


# ============================================================
# DATE FOR FOLDER
# ============================================================

def folder_date(date_str):

    day, month, year = date_str.split("/")

    return f"{day}-{month}-{year}"


# ============================================================
# DRIVER
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
            f"[i] Using Chrome profile: {PROFILE_DIR}"
        )

    else:

        print(
            "[i] Chrome profile not found."
        )

        print(
            "[i] Using a fresh Chrome profile."
        )

    return uc.Chrome(
        options=options,
        headless=False,
        use_subprocess=True
    )


# ============================================================
# PAGE DETECTION
# ============================================================

def find_page_element(driver):

    try:

        body_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).text.lower()

        if (
            "connection is slow" in body_text
            or
            "please wait" in body_text
        ):

            print()
            print(
                "[!] Eenadu is showing the "
                "'slow connection' screen."
            )
            print()

            return None, "blocked"

    except Exception:
        pass

    for elem_id in [
        "ImageContainer",
        "imgmain1",
        "homeMainImgBox",
    ]:

        try:

            element = driver.find_element(
                By.ID,
                elem_id
            )

            if (
                element.size["width"] > 400
                and
                element.size["height"] > 400
            ):

                return element, elem_id

        except Exception:
            pass

    return None, None


# ============================================================
# IMAGE SOURCE
# ============================================================

def get_image_src(driver):

    try:

        return (
            driver
            .find_element(
                By.ID,
                "imgmain1"
            )
            .get_attribute("src")
            or ""
        )

    except Exception:

        return ""


# ============================================================
# PAGE NUMBER FROM IMAGE URL
# ============================================================

def page_number_from_src(src):

    if not src:
        return None

    patterns = [
        r"_(\d{2,3})_hr\.(?:jpg|jpeg|png)",
        r"[_/-](\d{1,3})_hr",
        r"page[_-]?(\d{1,3})",
        r"Page[_-]?(\d{1,3})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            src,
            re.IGNORECASE
        )

        if match:

            try:
                return int(match.group(1))
            except Exception:
                pass

    return None


# ============================================================
# GET PAGE NUMBERS FROM PAGE LABELS
# ============================================================

def get_page_numbers_from_labels(driver):

    try:

        numbers = driver.execute_script(
            """
            const found = [];

            function addNumber(value) {

                const n = parseInt(value, 10);

                if (
                    Number.isInteger(n) &&
                    n >= 1 &&
                    n <= 100
                ) {
                    found.push(n);
                }
            }

            const elements =
                document.querySelectorAll('*');

            for (const el of elements) {

                const text =
                    (el.innerText || '')
                    .trim()
                    .replace(/\\s+/g, ' ');

                if (!text)
                    continue;

                if (text.length > 80)
                    continue;

                /*
                 * Examples:
                 *
                 * 01: Page
                 * 02: Page
                 * 03: Page
                 *
                 * 01 Page
                 * 02 Page
                 *
                 * 01
                 * 02
                 * 03
                 */

                let match =
                    text.match(
                        /^(\\d{1,3})\\s*[:.-]\\s*Page$/i
                    );

                if (match) {
                    addNumber(match[1]);
                    continue;
                }

                match =
                    text.match(
                        /^(\\d{1,3})\\s+Page$/i
                    );

                if (match) {
                    addNumber(match[1]);
                    continue;
                }

                if (
                    /^\\d{1,3}$/.test(text)
                ) {
                    addNumber(text);
                }
            }

            return [...new Set(found)];
            """
        )

        if numbers:

            return sorted(
                set(
                    int(n)
                    for n in numbers
                    if 1 <= int(n) <= MAX_PAGES
                )
            )

    except Exception:
        pass

    return []


# ============================================================
# GET PAGE NUMBERS FROM IMAGES / THUMBNAILS
# ============================================================

def get_page_numbers_from_images(driver):

    try:

        numbers = driver.execute_script(
            """
            const found = [];

            function addNumber(value) {

                const n =
                    parseInt(value, 10);

                if (
                    Number.isInteger(n) &&
                    n >= 1 &&
                    n <= 100
                ) {
                    found.push(n);
                }
            }

            const images =
                document.querySelectorAll('img');

            for (const img of images) {

                const values = [

                    img.getAttribute('src'),

                    img.getAttribute('data-src'),

                    img.getAttribute('data-page'),

                    img.getAttribute('page'),

                    img.getAttribute('alt'),

                    img.getAttribute('title')
                ];

                for (const value of values) {

                    if (!value)
                        continue;

                    const text =
                        String(value);

                    let match =
                        text.match(
                            /_(\\d{1,3})_hr\\./i
                        );

                    if (match) {
                        addNumber(match[1]);
                        continue;
                    }

                    match =
                        text.match(
                            /page[_-]?(\\d{1,3})/i
                        );

                    if (match) {
                        addNumber(match[1]);
                        continue;
                    }

                    match =
                        text.match(
                            /(?:^|\\D)(\\d{1,3})(?:\\D|$)/
                        );

                    if (
                        match &&
                        (
                            text.includes('Page') ||
                            text.includes('page') ||
                            text.includes('PAGE')
                        )
                    ) {
                        addNumber(match[1]);
                    }
                }
            }

            return [...new Set(found)];
            """
        )

        if numbers:

            return sorted(
                set(
                    int(n)
                    for n in numbers
                    if 1 <= int(n) <= MAX_PAGES
                )
            )

    except Exception:
        pass

    return []


# ============================================================
# GET PAGE NUMBERS FROM LINKS / BUTTONS
# ============================================================

def get_page_numbers_from_controls(driver):

    try:

        numbers = driver.execute_script(
            """
            const found = [];

            function addNumber(value) {

                const n =
                    parseInt(value, 10);

                if (
                    Number.isInteger(n) &&
                    n >= 1 &&
                    n <= 100
                ) {
                    found.push(n);
                }
            }

            const elements =
                document.querySelectorAll(
                    'a,button,span,li,div'
                );

            for (const el of elements) {

                const text =
                    (el.innerText || '')
                    .trim()
                    .replace(/\\s+/g, ' ');

                if (!text)
                    continue;

                if (text.length > 50)
                    continue;

                const id =
                    el.id || '';

                const cls =
                    typeof el.className === 'string'
                    ? el.className
                    : '';

                const combined =
                    (
                        text + ' ' +
                        id + ' ' +
                        cls
                    ).toLowerCase();

                if (
                    !combined.includes('page') &&
                    !combined.includes('thumb')
                ) {
                    continue;
                }

                const matches =
                    text.match(/\\d{1,3}/g);

                if (!matches)
                    continue;

                for (const m of matches) {
                    addNumber(m);
                }
            }

            return [...new Set(found)];
            """
        )

        if numbers:

            return sorted(
                set(
                    int(n)
                    for n in numbers
                    if 1 <= int(n) <= MAX_PAGES
                )
            )

    except Exception:
        pass

    return []


# ============================================================
# TOTAL PAGE COUNT
# ============================================================

def get_total_pages(driver):

    print()
    print(
        "[i] Detecting available newspaper pages..."
    )

    # --------------------------------------------------------
    # Method 1
    # Page labels
    # --------------------------------------------------------

    numbers = get_page_numbers_from_labels(
        driver
    )

    if numbers:

        highest = max(numbers)

        print(
            f"[i] Page labels detected: "
            f"{len(numbers)} entries"
        )

        print(
            f"[i] Highest page number: "
            f"{highest}"
        )

        return highest

    # --------------------------------------------------------
    # Method 2
    # Images / thumbnails
    # --------------------------------------------------------

    numbers = get_page_numbers_from_images(
        driver
    )

    if numbers:

        highest = max(numbers)

        print(
            f"[i] Thumbnail images detected: "
            f"{len(numbers)} entries"
        )

        print(
            f"[i] Highest page number: "
            f"{highest}"
        )

        return highest

    # --------------------------------------------------------
    # Method 3
    # Page controls
    # --------------------------------------------------------

    numbers = get_page_numbers_from_controls(
        driver
    )

    if numbers:

        highest = max(numbers)

        print(
            f"[i] Page controls detected: "
            f"{len(numbers)} entries"
        )

        print(
            f"[i] Highest page number: "
            f"{highest}"
        )

        return highest

    # --------------------------------------------------------
    # Method 4
    # Current image URL
    # --------------------------------------------------------

    current_src = get_image_src(
        driver
    )

    current_page = page_number_from_src(
        current_src
    )

    if current_page:

        print(
            f"[i] Current page detected "
            f"from image URL: {current_page}"
        )

    # --------------------------------------------------------
    # Method 5
    # Inspect common page-related attributes
    # --------------------------------------------------------

    try:

        numbers = driver.execute_script(
            """
            const found = [];

            function add(value) {

                const n =
                    parseInt(value, 10);

                if (
                    Number.isInteger(n) &&
                    n >= 1 &&
                    n <= 100
                ) {
                    found.push(n);
                }
            }

            const all =
                document.querySelectorAll('*');

            for (const el of all) {

                const attrs = [
                    'data-page',
                    'data-pageno',
                    'data-page-no',
                    'data-page-number',
                    'page',
                    'pageno',
                    'pageNo',
                    'pageNumber'
                ];

                for (const attr of attrs) {

                    const value =
                        el.getAttribute(attr);

                    if (value) {
                        add(value);
                    }
                }
            }

            return [...new Set(found)];
            """
        )

        if numbers:

            highest = max(numbers)

            print(
                f"[i] Page attributes detected."
            )

            print(
                f"[i] Highest page number: "
                f"{highest}"
            )

            return highest

    except Exception:
        pass

    # --------------------------------------------------------
    # Nothing found
    # --------------------------------------------------------

    print(
        "[!] Automatic page count detection "
        "could not determine the total."
    )

    return None


# ============================================================
# WAIT FOR PAGE
# ============================================================

def wait_for_page_ready(
    driver,
    timeout=15
):

    end_time = (
        time.time() + timeout
    )

    while time.time() < end_time:

        try:

            state = driver.execute_script(
                """
                const img =
                    document.querySelector(
                        '#imgmain1'
                    );

                if (!img)
                    return 'no-img';

                if (!img.complete)
                    return 'loading';

                if (img.naturalWidth < 100)
                    return 'tiny';

                return 'ready';
                """
            )

            if state == "ready":

                return True

        except Exception:
            pass

        time.sleep(0.4)

    return False


# ============================================================
# WAIT FOR PAGE CHANGE
# ============================================================

def wait_for_src_change(
    driver,
    old_src,
    timeout=WAIT_FOR_TURN_TIMEOUT
):

    end_time = (
        time.time() + timeout
    )

    while time.time() < end_time:

        new_src = get_image_src(
            driver
        )

        if (
            new_src
            and
            new_src != old_src
            and
            "_hr" in new_src
        ):

            wait_for_page_ready(
                driver,
                timeout=10
            )

            return new_src

        time.sleep(0.4)

    return None


# ============================================================
# HIDE STICKY ELEMENTS
# ============================================================

def hide_sticky_overlays(driver):

    driver.execute_script(
        """
        window.__hidden_stack = [];

        document.querySelectorAll('*')
        .forEach(el => {

            try {

                const s =
                    window.getComputedStyle(el);

                if (
                    s.position === 'fixed'
                    ||
                    s.position === 'sticky'
                ) {

                    window.__hidden_stack.push(
                        [
                            el,
                            el.style.visibility
                        ]
                    );

                    el.style.visibility =
                        'hidden';
                }

            } catch(e) {}

        });
        """
    )

    time.sleep(0.2)


# ============================================================
# RESTORE STICKY ELEMENTS
# ============================================================

def restore_overlays(driver):

    driver.execute_script(
        """
        (window.__hidden_stack || [])
        .forEach(([el, vis]) => {

            try {
                el.style.visibility = vis;
            } catch(e) {}

        });

        window.__hidden_stack = [];
        """
    )


# ============================================================
# SCREENSHOT CAPTURE
# ============================================================

def capture(
    driver,
    element,
    path,
    scale=SCALE,
    crop_top=CROP_TOP_PX
):

    driver.execute_script(
        """
        arguments[0].scrollIntoView({
            block: 'start'
        });
        """,
        element
    )

    time.sleep(0.3)

    hide_sticky_overlays(
        driver
    )

    try:

        rect = driver.execute_script(
            """
            const r =
                arguments[0]
                .getBoundingClientRect();

            return {

                x:
                    r.left +
                    window.scrollX,

                y:
                    r.top +
                    window.scrollY,

                w:
                    r.width,

                h:
                    r.height
            };
            """,
            element
        )

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

                    "scale": scale,
                },
            }
        )

        png_bytes = base64.b64decode(
            result["data"]
        )

    finally:

        restore_overlays(
            driver
        )

    if crop_top > 0:

        image = Image.open(
            BytesIO(png_bytes)
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

        image.save(path)

    else:

        with open(
            path,
            "wb"
        ) as file:

            file.write(
                png_bytes
            )


# ============================================================
# NEXT PAGE
# ============================================================

def try_next_page(driver):

    # --------------------------------------------------------
    # First: keyboard
    # --------------------------------------------------------

    try:

        driver.find_element(
            By.TAG_NAME,
            "body"
        ).send_keys(
            Keys.ARROW_RIGHT
        )

        return "arrow-key"

    except Exception:
        pass

    # --------------------------------------------------------
    # Second: next button
    # --------------------------------------------------------

    try:

        button = driver.find_element(
            By.XPATH,
            """
            //*
            [
                contains(@id,'next')
                or
                contains(@class,'next')
                or
                contains(@src,'right')
                or
                contains(@alt,'next')
                or
                contains(@onclick,'next')
            ]
            """
        )

        button.click()

        return "next-button"

    except Exception:
        return None


# ============================================================
# SHOW EDITIONS
# ============================================================

def show_editions():

    names = list(
        EDITIONS.keys()
    )

    print()
    print("=" * 70)
    print("AVAILABLE EENADU EDITIONS")
    print("=" * 70)
    print()

    for index, name in enumerate(
        names,
        start=1
    ):

        print(
            f"{index:2}) {name}"
        )

    print()
    print("=" * 70)

    while True:

        choice = input(
            "Enter edition number: "
        ).strip()

        try:

            number = int(choice)

        except ValueError:

            print(
                "[!] Please enter a number."
            )

            continue

        if (
            1 <= number <= len(names)
        ):

            selected_name = (
                names[number - 1]
            )

            return (
                selected_name,
                EDITIONS[selected_name]
            )

        print(
            f"[!] Enter a number between "
            f"1 and {len(names)}."
        )


# ============================================================
# DOWNLOAD EDITION
# ============================================================

def download_edition(
    driver,
    date_str,
    edition_name,
    edition_data
):

    eid = edition_data["eid"]

    pid = edition_data["pid"]

    # --------------------------------------------------------
    # URL
    # --------------------------------------------------------

    url = (
        "https://epaper.eenadu.net/Home/Index"
        f"?date={date_str}"
        f"&eid={eid}"
        f"&pid={pid}"
    )

    # --------------------------------------------------------
    # Output folder
    # --------------------------------------------------------

    date_folder = folder_date(
        date_str
    )

    output_dir = os.path.join(
        EDITION_OUTPUT_BASE,
        date_folder,
        edition_name
    )

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Information
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("SELECTED EDITION")
    print("=" * 70)

    print(
        f"Edition : {edition_name}"
    )

    print(
        f"EID     : {eid}"
    )

    print(
        f"PID     : {pid}"
    )

    print(
        f"Date    : {date_str}"
    )

    print()

    print(
        f"Output  : {output_dir}"
    )

    print()

    print(
        f"URL     : {url}"
    )

    print("=" * 70)
    print()

    # --------------------------------------------------------
    # Open
    # --------------------------------------------------------

    print(
        "[i] Opening Eenadu..."
    )

    driver.get(url)

    print(
        f"[i] Waiting "
        f"{WAIT_AFTER_INITIAL_LOAD}s "
        f"for the viewer..."
    )

    time.sleep(
        WAIT_AFTER_INITIAL_LOAD
    )

    # --------------------------------------------------------
    # Detect page
    # --------------------------------------------------------

    element, element_id = (
        find_page_element(driver)
    )

    if element_id == "blocked":

        print()

        print(
            "[!] Eenadu displayed "
            "a connection/verification screen."
        )

        print()

        input(
            ">>> Complete it in Chrome, "
            "then press ENTER... "
        )

        # Try again after user interaction

        element, element_id = (
            find_page_element(driver)
        )

    if not element:

        print()

        print(
            "[!] Newspaper page was "
            "not detected."
        )

        input(
            ">>> Press ENTER to close browser..."
        )

        return

    print(
        f"[i] Page detected via "
        f"#{element_id}"
    )

    # --------------------------------------------------------
    # Wait for first image
    # --------------------------------------------------------

    print(
        "[i] Waiting for first page image..."
    )

    wait_for_page_ready(
        driver,
        timeout=20
    )

    # --------------------------------------------------------
    # Detect page count
    # --------------------------------------------------------

    detected_pages = (
        get_total_pages(driver)
    )

    # --------------------------------------------------------
    # If automatic detection worked
    # --------------------------------------------------------

    if (
        detected_pages
        and
        detected_pages > 1
    ):

        num_pages = detected_pages

        print()

        print(
            f"[i] Auto-detected "
            f"{num_pages} pages."
        )

    else:

        print()

        print(
            "[!] Automatic page count "
            "detection failed."
        )

        print()

        manual = input(
            "Enter number of pages: "
        ).strip()

        try:

            num_pages = int(
                manual
            )

        except ValueError:

            print(
                "[!] Invalid page count."
            )

            return

        if (
            num_pages < 1
            or
            num_pages > MAX_PAGES
        ):

            print(
                f"[!] Page count must be "
                f"between 1 and {MAX_PAGES}."
            )

            return

    # --------------------------------------------------------
    # Start capture
    # --------------------------------------------------------

    print()

    input(
        ">>> Press ENTER to begin capture "
        "(set viewer zoom to 100% if required)... "
    )

    print()

    captured = 0

    # --------------------------------------------------------
    # Capture loop
    # --------------------------------------------------------

    for page in range(
        1,
        num_pages + 1
    ):

        # --------------------------------------------
        # Find page element again
        # --------------------------------------------

        element, element_id = (
            find_page_element(driver)
        )

        if element_id == "blocked":

            print(
                f"  page {page}: "
                f"blocked. Stopping."
            )

            break

        if not element:

            print(
                f"  page {page}: "
                f"page element not found."
            )

            break

        # --------------------------------------------
        # Wait for image
        # --------------------------------------------

        wait_for_page_ready(
            driver,
            timeout=15
        )

        # --------------------------------------------
        # Current image
        # --------------------------------------------

        current_src = (
            get_image_src(driver)
        )

        # --------------------------------------------
        # Output path
        # --------------------------------------------

        path = os.path.join(
            output_dir,
            f"page_{page:03d}.png"
        )

        # --------------------------------------------
        # Capture
        # --------------------------------------------

        capture(
            driver,
            element,
            path
        )

        captured += 1

        print(
            f"  page {page:03d} "
            f"captured -> {path}"
        )

        # --------------------------------------------
        # Last page
        # --------------------------------------------

        if page >= num_pages:

            break

        # --------------------------------------------
        # Next page
        # --------------------------------------------

        method = try_next_page(
            driver
        )

        if not method:

            print(
                f"  page {page}: "
                f"could not turn page."
            )

            break

        print(
            f"       next: {method}"
        )

        # --------------------------------------------
        # Wait
        # --------------------------------------------

        time.sleep(
            WAIT_AFTER_TURN
        )

        # --------------------------------------------
        # Wait for image change
        # --------------------------------------------

        new_src = (
            wait_for_src_change(
                driver,
                current_src,
                timeout=WAIT_FOR_TURN_TIMEOUT
            )
        )

        # --------------------------------------------
        # Second chance
        # --------------------------------------------

        if not new_src:

            print(
                "       waiting a little longer..."
            )

            time.sleep(3)

            new_src = (
                wait_for_src_change(
                    driver,
                    current_src,
                    timeout=8
                )
            )

        # --------------------------------------------
        # Stop duplicate capture
        # --------------------------------------------

        if not new_src:

            print()

            print(
                f"  page {page}: "
                f"image did not change."
            )

            print(
                "[!] Stopping to avoid "
                "duplicate screenshots."
            )

            break

    # --------------------------------------------------------
    # Create PDF and delete screenshots after successful PDF
    # --------------------------------------------------------

    pdf_path = None

    if captured > 0:
        pdf_path = create_pdf_from_screenshots(
            output_dir,
            date_str,
            edition_name
        )
    else:
        print()
        print(
            "[!] No pages were captured."
        )
        print(
            "[!] PDF creation skipped."
        )

    # --------------------------------------------------------
    # Finished
    # --------------------------------------------------------

    print()

    print("=" * 70)
    print("DOWNLOAD COMPLETE")
    print("=" * 70)

    print(
        f"Edition : {edition_name}"
    )

    print(
        f"Date    : {date_str}"
    )

    print(
        f"Pages   : {captured}"
    )

    print(
        f"Folder  : {output_dir}"
    )

    if pdf_path:
        print(
            f"PDF     : {pdf_path}"
        )
        print(
            "[✓] Screenshots were automatically deleted "
            "after successful PDF creation."
        )
    else:
        print(
            "[!] PDF was not created."
        )
        print(
            "[!] Screenshots were kept."
        )

    print("=" * 70)
    print()



# ============================================================
# CREATE A4 PDF
# ============================================================

def create_pdf_from_screenshots(
    output_dir,
    date_str,
    edition_name
):
    """
    Create an A4 PDF from the captured PNG screenshots.

    The PDF is created first. Screenshots are deleted only after
    the PDF exists and has a non-zero file size.
    """

    screenshot_files = []

    for filename in os.listdir(output_dir):
        if re.match(r"^page_\d{3}\.png$", filename, re.IGNORECASE):
            screenshot_files.append(
                os.path.join(output_dir, filename)
            )

    screenshot_files.sort(
        key=lambda path: int(
            re.search(
                r"page_(\d{3})\.png$",
                os.path.basename(path),
                re.IGNORECASE
            ).group(1)
        )
    )

    if not screenshot_files:
        print()
        print("[!] No screenshots found for PDF creation.")
        return None

    date_folder = folder_date(date_str)

    pdf_path = os.path.join(
        output_dir,
        f"Eenadu {date_folder} {edition_name} A4.pdf"
    )

    print()
    print("=" * 70)
    print("CREATING A4 PDF")
    print("=" * 70)
    print(
        f"Pages : {len(screenshot_files)}"
    )
    print(
        f"PDF   : {pdf_path}"
    )
    print()

    # A4 at 300 DPI
    A4_WIDTH = 2480
    A4_HEIGHT = 3508

    pdf_pages = []

    try:
        for index, screenshot_path in enumerate(
            screenshot_files,
            start=1
        ):
            print(
                f"  PDF page {index:03d} -> "
                f"{os.path.basename(screenshot_path)}"
            )

            with Image.open(screenshot_path) as source:
                image = source.convert("RGB")

                # Preserve the original aspect ratio and fit the
                # newspaper page inside an A4 canvas.
                image.thumbnail(
                    (A4_WIDTH, A4_HEIGHT),
                    Image.Resampling.LANCZOS
                )

                canvas = Image.new(
                    "RGB",
                    (A4_WIDTH, A4_HEIGHT),
                    "white"
                )

                x = (
                    A4_WIDTH - image.width
                ) // 2

                y = (
                    A4_HEIGHT - image.height
                ) // 2

                canvas.paste(
                    image,
                    (x, y)
                )

                pdf_pages.append(canvas)

        first_page = pdf_pages[0]

        save_kwargs = {
            "save_all": True,
            "append_images": pdf_pages[1:],
            "resolution": 300.0,
            "title": f"Eenadu {date_folder} {edition_name}",
            "author": "Eenadu",
            "creator": "Eenadu",
            "subject": f"Eenadu {edition_name} e-paper",
        }

        first_page.save(
            pdf_path,
            "PDF",
            **save_kwargs
        )

        # Verify the PDF before deleting screenshots.
        if (
            not os.path.isfile(pdf_path)
            or
            os.path.getsize(pdf_path) <= 0
        ):
            print()
            print(
                "[!] PDF was not created correctly."
            )
            print(
                "[!] Screenshots will NOT be deleted."
            )
            return None

        print()
        print(
            "[✓] PDF created successfully."
        )
        print(
            f"[✓] PDF size: "
            f"{os.path.getsize(pdf_path):,} bytes"
        )

        # --------------------------------------------------------
        # AUTO DELETE SCREENSHOTS
        # --------------------------------------------------------

        deleted = 0

        print()
        print(
            "[i] PDF verified. Deleting screenshots..."
        )

        for screenshot_path in screenshot_files:
            try:
                os.remove(screenshot_path)
                deleted += 1
            except Exception as error:
                print(
                    f"[!] Could not delete "
                    f"{os.path.basename(screenshot_path)}: "
                    f"{error}"
                )

        print(
            f"[✓] Deleted {deleted} screenshot(s)."
        )

        return pdf_path

    except Exception as error:
        print()
        print(
            "[!] PDF creation failed:"
        )
        print(
            error
        )
        print(
            "[!] Screenshots were kept."
        )

        return None


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) < 2:

        print()

        print(
            "Usage:"
        )

        print(
            "python editions.py DD/MM/YYYY"
        )

        print()

        print(
            "Example:"
        )

        print(
            "python editions.py 27/09/2026"
        )

        print()

        sys.exit(1)

    date_str = sys.argv[1]

    # --------------------------------------------------------
    # Validate date
    # --------------------------------------------------------

    if not validate_date(
        date_str
    ):

        print()

        print(
            "[!] Invalid date."
        )

        print(
            "Use DD/MM/YYYY."
        )

        print(
            "Example: 27/09/2026"
        )

        print()

        sys.exit(1)

    # --------------------------------------------------------
    # Select edition
    # --------------------------------------------------------

    edition_name, edition_data = (
        show_editions()
    )

    # --------------------------------------------------------
    # Start Chrome
    # --------------------------------------------------------

    driver = build_driver()

    try:

        download_edition(
            driver,
            date_str,
            edition_name,
            edition_data
        )

    except KeyboardInterrupt:

        print()

        print(
            "[!] Stopped by user."
        )

    except Exception as error:

        print()

        print(
            "[!] Unexpected error:"
        )

        print(
            error
        )

        import traceback

        traceback.print_exc()

        input(
            ">>> Press ENTER to close browser..."
        )

    finally:

        try:

            driver.quit()

        except Exception:
            pass


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
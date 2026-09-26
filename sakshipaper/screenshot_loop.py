# ============================================================
# Newspaper E-Paper Automation
# Open Source Project
# Copyright (c) 2026
#
# Licensed under the MIT License.
# See LICENSE file for details.
# ============================================================

r"""
Sakshi e-paper: capture all pages as full-page screenshots.

Usage:
    python screenshot_loop.py DD/MM/YYYY

Example:
    python screenshot_loop.py 26/09/2026
"""

import os
import sys
import time
import base64

import undetected_chromedriver as uc

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    UnexpectedAlertPresentException,
    NoAlertPresentException,
)


# ============================================================
# CONFIG
# ============================================================

URL_TEMPLATE = (
    "https://epaper.sakshi.com/Telangana_Main"
    "?eid=216&edate={date}&device=desktop&view=3"
)

# ============================================================
# PROJECT PATH
# ============================================================

# This script is expected to be inside:
# C:\newspaper\sakshipaper

BASE_DIR = r"C:\newspaper\sakshipaper"

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "pages_shot"
)

PROFILE_DIR = os.path.join(
    BASE_DIR,
    "chrome_profile"
)


# ============================================================
# SCREENSHOT SETTINGS
# ============================================================

SCALE = 2


# ============================================================
# WAITING SETTINGS
# ============================================================

WAIT_AFTER_INITIAL_LOAD = 30
WAIT_AFTER_TURN = 3
WAIT_FOR_TURN_TIMEOUT = 15


# ============================================================
# MAXIMUM PAGES
# ============================================================

MAX_PAGES = 60


# ============================================================
# DATE
# ============================================================

def get_date_from_command_line():
    """
    Get newspaper date from command line.

    Example:
        python screenshot_loop.py 26/09/2026
    """

    if len(sys.argv) < 2:

        print()
        print("Usage:")
        print("  python screenshot_loop.py DD/MM/YYYY")
        print()
        print("Example:")
        print("  python screenshot_loop.py 26/09/2026")
        print()

        sys.exit(1)


    date = sys.argv[1].strip()


    # --------------------------------------------------------
    # Validate date format
    # --------------------------------------------------------

    parts = date.split("/")


    if len(parts) != 3:

        print(f"[!] Invalid date: {date}")
        print("    Required format: DD/MM/YYYY")
        print("    Example: 26/09/2026")

        sys.exit(1)


    day, month, year = parts


    if (
        len(day) != 2
        or len(month) != 2
        or len(year) != 4
        or not day.isdigit()
        or not month.isdigit()
        or not year.isdigit()
    ):

        print(f"[!] Invalid date: {date}")
        print("    Required format: DD/MM/YYYY")
        print("    Example: 26/09/2026")

        sys.exit(1)


    day = int(day)
    month = int(month)
    year = int(year)


    if not (1 <= day <= 31):

        print(f"[!] Invalid day: {day}")

        sys.exit(1)


    if not (1 <= month <= 12):

        print(f"[!] Invalid month: {month}")

        sys.exit(1)


    return date


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


    # Create Chrome profile directory

    os.makedirs(
        PROFILE_DIR,
        exist_ok=True
    )


    options.add_argument(
        f"--user-data-dir={PROFILE_DIR}"
    )

    options.add_argument(
        "--profile-directory=Default"
    )


    print(
        f"[i] Using Chrome profile:"
    )

    print(
        f"    {PROFILE_DIR}\\Default"
    )


    return uc.Chrome(
        options=options,
        headless=False,
        use_subprocess=True
    )


# ============================================================
# ALERT HANDLING
# ============================================================

def dismiss_alert(driver):

    try:

        alert = driver.switch_to.alert

        text = alert.text

        print(
            f"    [alert] {text}"
        )

        alert.accept()

        return text


    except NoAlertPresentException:

        return None


    except Exception:

        return None


# ============================================================
# PAGE DETECTION
# ============================================================

def find_page_element(driver):

    for elem_id in [
        "ImageContainer",
        "ImageContainerDiv",
        "imgmain1"
    ]:

        try:

            el = driver.find_element(
                By.ID,
                elem_id
            )


            r = el.rect


            if (
                r["width"] > 400
                and r["height"] > 400
            ):

                return el, elem_id


        except UnexpectedAlertPresentException:

            dismiss_alert(driver)

            return None, "end"


        except Exception:

            pass


    return None, None


# ============================================================
# GET IMAGE URL
# ============================================================

def get_image_src(driver):

    try:

        return driver.execute_script(
            """
            return (
                document.getElementById('imgmain1') || {}
            ).src || '';
            """
        ) or ""


    except UnexpectedAlertPresentException:

        dismiss_alert(driver)

        return ""


# ============================================================
# WAIT FOR PAGE READY
# ============================================================

def wait_for_page_ready(
    driver,
    timeout=15
):

    end = time.time() + timeout


    while time.time() < end:

        try:

            state = driver.execute_script(
                """
                const a =
                    document.querySelector('#imgmain1');

                const b =
                    document.querySelector('#imgmain2');


                if (!a || !b)
                    return 'no-img';


                if (!a.complete || !b.complete)
                    return 'loading';


                if (a.naturalWidth < 100)
                    return 'tiny';


                return 'ready';
                """
            )


            if state == "ready":

                return True


        except UnexpectedAlertPresentException:

            dismiss_alert(driver)

            return False


        except Exception:

            pass


        time.sleep(0.4)


    return False


# ============================================================
# WAIT FOR IMAGE CHANGE
# ============================================================

def wait_for_src_change(
    driver,
    old_src,
    timeout=WAIT_FOR_TURN_TIMEOUT
):

    end = time.time() + timeout


    while time.time() < end:

        new_src = get_image_src(driver)


        if not new_src:

            time.sleep(0.3)

            continue


        if (
            new_src != old_src
            and "_hr" in new_src
        ):

            wait_for_page_ready(
                driver,
                timeout=10
            )

            return new_src


        time.sleep(0.4)


    return None


# ============================================================
# HIDE STICKY OVERLAYS
# ============================================================

def hide_sticky_overlays(driver):

    try:

        driver.execute_script(
            """
            window.__hidden_stack = [];

            const target =
                document.getElementById(
                    'ImageContainer'
                );


            function isProtected(el) {

                if (!target)
                    return false;


                let n = el;


                while (n) {

                    if (n === target)
                        return true;


                    n = n.parentElement;
                }


                n = target;


                while (n) {

                    if (n === el)
                        return true;


                    n = n.parentElement;
                }


                return false;
            }


            function hide(el) {

                try {

                    window.__hidden_stack.push([
                        el,
                        el.style.visibility,
                        el.style.display
                    ]);


                    el.style.visibility =
                        'hidden';


                    el.style.display =
                        'none';

                } catch(e) {}

            }


            document
                .querySelectorAll('*')
                .forEach(el => {

                    try {

                        if (isProtected(el))
                            return;


                        const s =
                            window.getComputedStyle(
                                el
                            );


                        const id =
                            (el.id || '')
                            .toLowerCase();


                        const cls =
                            (el.className || '')
                            .toString()
                            .toLowerCase();


                        const tag =
                            el.tagName;


                        if (
                            s.position === 'fixed' ||
                            s.position === 'sticky'
                        ) {

                            hide(el);

                            return;
                        }


                        if (tag === 'IFRAME') {

                            hide(el);

                            return;
                        }


                        if (
                            /(^|\\s|_|-)(ad|ads|adv|advert|banner|promo|skip|sponsor|popup|modal|overlay|interstitial)(\\s|_|-|$)/
                            .test(
                                id + ' ' + cls
                            )
                        ) {

                            hide(el);

                            return;
                        }


                        const z =
                            parseInt(
                                s.zIndex,
                                10
                            );


                        if (
                            s.position === 'absolute' &&
                            !isNaN(z) &&
                            z >= 100
                        ) {

                            hide(el);

                            return;
                        }


                    } catch(e) {}

                });


            document
                .querySelectorAll(
                    'button, a, span, div'
                )
                .forEach(el => {

                    try {

                        const t =
                            (
                                el.innerText || ''
                            ).trim();


                        if (
                            t === 'SKIP' ||
                            t === 'Skip' ||
                            t === 'Skip Ad' ||
                            t === 'Learn More'
                        ) {

                            let node = el;


                            for (
                                let i = 0;
                                i < 8 &&
                                node.parentElement;
                                i++
                            ) {

                                if (
                                    isProtected(
                                        node.parentElement
                                    )
                                )
                                    break;


                                node =
                                    node.parentElement;
                            }


                            if (
                                !isProtected(node)
                            )
                                hide(node);
                        }


                    } catch(e) {}

                });
            """
        )


        time.sleep(0.4)


    except Exception:

        pass


# ============================================================
# RESTORE OVERLAYS
# ============================================================

def restore_overlays(driver):

    try:

        driver.execute_script(
            """
            (window.__hidden_stack || [])
                .forEach(
                    ([el, vis, disp]) => {

                        try {

                            el.style.visibility =
                                vis;

                            el.style.display =
                                disp;

                        } catch(e) {}

                    }
                );


            window.__hidden_stack = [];
            """
        )


    except Exception:

        pass


# ============================================================
# CAPTURE SCREENSHOT
# ============================================================

def capture(
    driver,
    element,
    path,
    scale=SCALE
):

    try:

        driver.execute_script(
            """
            arguments[0]
                .scrollIntoView({
                    block: 'center'
                });
            """,
            element
        )


        time.sleep(0.3)


    except Exception:

        pass


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


    with open(
        path,
        "wb"
    ) as f:

        f.write(
            png_bytes
        )


# ============================================================
# NEXT PAGE
# ============================================================

def try_next_page(driver):

    try:

        driver.find_element(
            By.TAG_NAME,
            "body"
        ).send_keys(
            Keys.ARROW_RIGHT
        )


        return "arrow-key"


    except UnexpectedAlertPresentException:

        dismiss_alert(driver)

        return None


    except Exception:

        pass


    try:

        btn = driver.find_element(
            By.XPATH,
            "//*[contains(@id,'next') "
            "or contains(@class,'next') "
            "or contains(@src,'right') "
            "or contains(@alt,'next') "
            "or contains(@onclick,'next')]"
        )


        btn.click()


        return "next-button"


    except Exception:

        return None


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Get date
    # --------------------------------------------------------

    date = get_date_from_command_line()


    # --------------------------------------------------------
    # Build URL
    # --------------------------------------------------------

    url = URL_TEMPLATE.format(
        date=date
    )


    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )


    # --------------------------------------------------------
    # Display configuration
    # --------------------------------------------------------

    print()

    print("=" * 60)

    print("SAKSHI E-PAPER")

    print("=" * 60)

    print(
        f"Date       : {date}"
    )

    print(
        f"URL        : {url}"
    )

    print(
        f"Output     : {OUTPUT_DIR}"
    )

    print(
        f"Profile    : {PROFILE_DIR}"
    )

    print(
        f"Max pages  : {MAX_PAGES}"
    )

    print("=" * 60)

    print()


    # --------------------------------------------------------
    # Start Chrome
    # --------------------------------------------------------

    driver = build_driver()


    try:

        print(
            f"[i] Opening: {url}"
        )


        driver.get(
            url
        )


        print(
            f"[i] Waiting "
            f"{WAIT_AFTER_INITIAL_LOAD}s "
            f"for the viewer to load..."
        )


        time.sleep(
            WAIT_AFTER_INITIAL_LOAD
        )


        dismiss_alert(
            driver
        )


        # ----------------------------------------------------
        # Find newspaper page
        # ----------------------------------------------------

        element, eid = find_page_element(
            driver
        )


        if not element:

            print()

            print(
                "[!] Page not found."
            )

            print(
                "[!] If Sakshi asked you to log in, "
                "do it in the Chrome window."
            )


            input(
                ">>> Log in if needed, "
                "open the e-paper, "
                "then press ENTER... "
            )


            dismiss_alert(
                driver
            )


            element, eid = find_page_element(
                driver
            )


            if not element:

                print(
                    "[!] Still no page."
                )

                print(
                    "[!] Check the Sakshi URL "
                    "and date."
                )


                input(
                    ">>> Press Enter to close... "
                )


                return


        print(
            f"[i] Page detected via #{eid}."
        )


        input(
            ">>> Press Enter to begin capture "
            "(zoom viewer to 100% first)... "
        )


        # ----------------------------------------------------
        # Capture pages
        # ----------------------------------------------------

        captured = 0

        prev_src = None

        stale = 0


        for page in range(
            1,
            MAX_PAGES + 1
        ):


            element, eid = find_page_element(
                driver
            )


            if (
                eid == "end"
                or not element
            ):

                print(
                    f"  page {page}: "
                    "no page element "
                    "(end of edition)."
                )

                break


            wait_for_page_ready(
                driver,
                timeout=15
            )


            current_src = get_image_src(
                driver
            )


            # ------------------------------------------------
            # Duplicate page detection
            # ------------------------------------------------

            if (
                current_src
                and current_src == prev_src
            ):

                stale += 1


                if stale >= 3:

                    print(
                        "  no new page after "
                        "3 tries, stopping."
                    )

                    break


            else:

                stale = 0


            prev_src = current_src


            # ------------------------------------------------
            # Screenshot filename
            # ------------------------------------------------

            path = os.path.join(
                OUTPUT_DIR,
                f"page_{page:03d}.png"
            )


            # ------------------------------------------------
            # Capture
            # ------------------------------------------------

            capture(
                driver,
                element,
                path
            )


            captured += 1


            print(
                f"  page {page:02d} "
                f"captured -> {path}"
            )


            # ------------------------------------------------
            # Go to next page
            # ------------------------------------------------

            how = try_next_page(
                driver
            )


            if not how:

                print(
                    f"  page {page}: "
                    "could not turn page "
                    "(alert = last page)."
                )

                break


            time.sleep(
                WAIT_AFTER_TURN
            )


            # ------------------------------------------------
            # Wait for new image
            # ------------------------------------------------

            new_src = wait_for_src_change(
                driver,
                current_src,
                timeout=WAIT_FOR_TURN_TIMEOUT
            )


            if not new_src:

                dismiss_alert(
                    driver
                )


                new_src = wait_for_src_change(
                    driver,
                    current_src,
                    timeout=5
                )


                if not new_src:

                    print(
                        f"  page {page}: "
                        "image src did not change, "
                        "stopping."
                    )

                    break


        # ----------------------------------------------------
        # Finished
        # ----------------------------------------------------

        print()

        print("=" * 60)

        print(
            f"All done. Captured {captured} pages."
        )

        print(
            f"Output folder:"
        )

        print(
            f"  {OUTPUT_DIR}"
        )

        print("=" * 60)


    finally:

        input(
            ">>> Press Enter to close the browser... "
        )


        try:

            driver.quit()

        except Exception:

            pass


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
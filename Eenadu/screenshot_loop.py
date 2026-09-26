# ============================================================
# Newspaper E-Paper Automation
# Open Source Project
# Copyright (c) 2026
#
# Licensed under the MIT License.
# See LICENSE file for details.
# ============================================================

r"""
Eenadu e-paper: capture all pages as full-page screenshots.

Uses undetected-chromedriver to bypass bot detection.
Auto-detects the actual number of pages so it won't capture duplicates.
Waits for the page image src to change before advancing, avoiding false
"stuck viewer" aborts.

Usage:
    python screenshot_loop.py <date> [num_pages] [pid]

Examples:
    python screenshot_loop.py 17/09/2026
    python screenshot_loop.py 17/09/2026 22
    python screenshot_loop.py 17/09/2026 22 3586231
"""

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

URL_TEMPLATE = "https://epaper.eenadu.net/Home/Index?date={date}&eid=1&pid={pid}"
OUTPUT_DIR = "pages_shot"
SCALE = 2
WAIT_AFTER_INITIAL_LOAD = 25
WAIT_AFTER_TURN = 3          # base wait, then we poll for src change
WAIT_FOR_TURN_TIMEOUT = 15   # max seconds to wait for the new page image
CROP_TOP_PX = 0

PROFILE_DIR = r"C:\newspaper\chrome_profile"


# ---------- Driver ----------
def build_driver():
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1800,2400")
    options.add_argument("--force-device-scale-factor=1")

    if os.path.isdir(PROFILE_DIR):
        options.add_argument(f"--user-data-dir={PROFILE_DIR}")
        options.add_argument("--profile-directory=Default")
        print(f"[i] Using profile: {PROFILE_DIR}")
    else:
        print(f"[i] No profile at {PROFILE_DIR} — using a fresh profile.")

    return uc.Chrome(options=options, headless=False, use_subprocess=True)


# ---------- Page detection ----------
def find_page_element(driver):
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        if "connection is slow" in body_text or "please wait" in body_text:
            print("\n[!] Eenadu is showing the 'slow connection' bot-block screen.\n")
            return None, "blocked"
    except Exception:
        pass

    for elem_id in ["ImageContainer", "imgmain1", "homeMainImgBox"]:
        try:
            el = driver.find_element(By.ID, elem_id)
            if el.size["width"] > 400 and el.size["height"] > 400:
                return el, elem_id
        except Exception:
            pass
    return None, None


def get_image_src(driver):
    """Return the current src of #imgmain1."""
    try:
        return driver.find_element(By.ID, "imgmain1").get_attribute("src") or ""
    except Exception:
        return ""


def page_number_from_src(src):
    """Extract page number from the image src, e.g. ..._05_hr.jpg -> 5."""
    if not src:
        return None
    m = re.search(r'_(\d{2})_hr\.(?:jpg|png)', src)
    if m:
        return int(m.group(1))
    return None


def get_total_pages(driver):
    """Read the highest page number from thumbnail strip labels."""
    try:
        nums = driver.execute_script("""
            const nums = [];
            const rx = /^(\\d{1,3})\\s*[-:.]?\\s*(Page|FRONT PAGE|BACK PAGE|[A-Z ]+)$/i;
            document.querySelectorAll('*').forEach(el => {
                if (el.children.length > 0) return;
                const t = (el.innerText || '').trim();
                if (!t || t.length > 30) return;
                const m = t.match(rx);
                if (m) nums.push(parseInt(m[1], 10));
            });
            return nums;
        """)
        if nums:
            return max(nums)
    except Exception:
        pass
    return None


def wait_for_page_ready(driver, timeout=15):
    """Poll until #imgmain1 is complete and has real content."""
    end = time.time() + timeout
    while time.time() < end:
        try:
            state = driver.execute_script("""
                const img = document.querySelector('#imgmain1');
                if (!img) return 'no-img';
                if (!img.complete) return 'loading';
                if (img.naturalWidth < 100) return 'tiny';
                return 'ready';
            """)
            if state == 'ready':
                return True
        except Exception:
            pass
        time.sleep(0.4)
    return False


def wait_for_src_change(driver, old_src, timeout=WAIT_FOR_TURN_TIMEOUT):
    """Poll until #imgmain1's src changes to a different page, or timeout."""
    end = time.time() + timeout
    while time.time() < end:
        new_src = get_image_src(driver)
        if new_src and new_src != old_src and "_hr" in new_src:
            # Also make sure the new image has loaded
            wait_for_page_ready(driver, timeout=10)
            return new_src
        time.sleep(0.4)
    return None


# ---------- Overlay hiding ----------
def hide_sticky_overlays(driver):
    driver.execute_script("""
        window.__hidden_stack = [];
        document.querySelectorAll('*').forEach(el => {
            try {
                const s = window.getComputedStyle(el);
                if (s.position === 'fixed' || s.position === 'sticky') {
                    window.__hidden_stack.push([el, el.style.visibility]);
                    el.style.visibility = 'hidden';
                }
            } catch(e) {}
        });
    """)
    time.sleep(0.2)


def restore_overlays(driver):
    driver.execute_script("""
        (window.__hidden_stack || []).forEach(([el, vis]) => {
            try { el.style.visibility = vis; } catch(e) {}
        });
        window.__hidden_stack = [];
    """)


# ---------- Capture ----------
def capture(driver, element, path, scale=SCALE, crop_top=CROP_TOP_PX):
    driver.execute_script("arguments[0].scrollIntoView({block:'start'});", element)
    time.sleep(0.3)

    hide_sticky_overlays(driver)
    try:
        rect = driver.execute_script("""
            const r = arguments[0].getBoundingClientRect();
            return {
                x: r.left + window.scrollX,
                y: r.top  + window.scrollY,
                w: r.width,
                h: r.height
            };
        """, element)

        result = driver.execute_cdp_cmd("Page.captureScreenshot", {
            "format": "png",
            "captureBeyondViewport": True,
            "clip": {
                "x": rect["x"], "y": rect["y"],
                "width": rect["w"], "height": rect["h"],
                "scale": scale,
            }
        })
        png_bytes = base64.b64decode(result["data"])
    finally:
        restore_overlays(driver)

    if crop_top > 0:
        img = Image.open(BytesIO(png_bytes))
        w, h = img.size
        img = img.crop((0, crop_top, w, h))
        img.save(path)
    else:
        with open(path, "wb") as f:
            f.write(png_bytes)


# ---------- Page turn ----------
def try_next_page(driver):
    """Try keyboard and click fallbacks. Returns the method used, or None."""
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ARROW_RIGHT)
        return "arrow-key"
    except Exception:
        pass
    try:
        btn = driver.find_element(By.XPATH,
            "//*[contains(@id,'next') or contains(@class,'next') "
            "or contains(@src,'right') or contains(@alt,'next') "
            "or contains(@onclick,'next')]")
        btn.click()
        return "next-button"
    except Exception:
        return None


# ---------- Main ----------
def main():
    if len(sys.argv) < 2:
        print("Usage: python screenshot_loop.py <date> [num_pages] [pid]")
        sys.exit(1)
    date_str = sys.argv[1]
    num_pages_arg = int(sys.argv[2]) if len(sys.argv) > 2 else None
    pid = sys.argv[3] if len(sys.argv) > 3 else "0"

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    url = URL_TEMPLATE.format(date=date_str, pid=pid)

    driver = build_driver()

    try:
        print(f"Opening: {url}")
        driver.get(url)

        print(f"[i] Waiting {WAIT_AFTER_INITIAL_LOAD}s for the viewer to load...")
        time.sleep(WAIT_AFTER_INITIAL_LOAD)

        element, eid = find_page_element(driver)
        if eid == "blocked":
            input(">>> Press Enter to close the browser... ")
            return
        if not element:
            print("[!] Page element not found after initial load.")
            input(">>> Press Enter to close the browser... ")
            return

        print(f"[i] Page detected via #{eid}.")

        # Determine page count
        detected = get_total_pages(driver)
        if detected and detected > 1:
            num_pages = detected
            print(f"[i] Auto-detected {num_pages} pages in this edition.")
        elif num_pages_arg:
            num_pages = num_pages_arg
            print(f"[i] Could not auto-detect. Using argument: {num_pages} pages.")
        else:
            print("[!] Could not auto-detect page count and no argument given.")
            input(">>> Press Enter to close the browser... ")
            return

        input(">>> Press Enter here to begin capture (zoom the viewer to 100% first)... ")

        captured = 0
        for page in range(1, num_pages + 1):
            element, eid = find_page_element(driver)
            if eid == "blocked":
                print(f"  page {page}: blocked — stopping.")
                break
            if not element:
                print(f"  page {page}: no page element found, stopping.")
                break

            wait_for_page_ready(driver, timeout=15)
            current_src = get_image_src(driver)

            path = os.path.join(OUTPUT_DIR, f"page_{page:03d}.png")
            capture(driver, element, path)
            captured += 1
            print(f"  page {page:02d} captured -> {path}")

            if page >= num_pages:
                break

            # Turn the page and wait for the src to actually change
            how = try_next_page(driver)
            if not how:
                print(f"  page {page}: could not turn page. Stopping.")
                break

            time.sleep(WAIT_AFTER_TURN)
            new_src = wait_for_src_change(driver, current_src,
                                          timeout=WAIT_FOR_TURN_TIMEOUT)
            if not new_src:
                # Verify it's genuinely stuck, not just slow
                time.sleep(3)
                new_src = wait_for_src_change(driver, current_src, timeout=8)

            if not new_src:
                print(f"  page {page}: image src did not change "
                      f"within timeout. Stopping.")
                break

        print(f"\nAll done. Captured {captured} pages in {OUTPUT_DIR}/")

    finally:
        input(">>> Press Enter to close the browser... ")
        driver.quit()


if __name__ == "__main__":
    main()
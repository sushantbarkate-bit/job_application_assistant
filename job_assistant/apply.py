"""Playwright form helper. It intentionally never clicks Submit/Apply."""
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

class FormFiller:
    def __init__(self, allowed_domains: list[str], headless=False):
        self.allowed_domains = {d.lower() for d in allowed_domains}
        self.headless = headless

    def inspect_and_fill(self, url: str, values: dict[str, str], resume_path: str | None = None):
        host = (urlparse(url).hostname or "").lower()
        if not host or not any(host == d or host.endswith("." + d) for d in self.allowed_domains):
            raise ValueError(f"Domain {host!r} is not allowlisted in config.yaml. No browser opened.")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            # Conservative matching by label/name/placeholder. Unknown questions are left blank.
            for key, value in values.items():
                locator = page.get_by_label(key, exact=False)
                if locator.count() == 0:
                    locator = page.locator(f'input[name*="{key}" i], textarea[name*="{key}" i]').first
                if locator.count() and locator.is_visible():
                    try: locator.fill(value)
                    except Exception: pass
            if resume_path:
                uploads = page.locator('input[type="file"]')
                if uploads.count():
                    try: uploads.first.set_input_files(resume_path)
                    except Exception: pass
            title = page.title()
            browser.close()
        return {"page_title": title, "filled_fields": list(values.keys()), "submitted": False,
                "note": "Form inspected/filled. Submit manually after reviewing the live page."}

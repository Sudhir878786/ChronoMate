# a.py
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import time

STORAGE_FILE = "storage_state.json"

def get_previous_day():
    today = datetime.today()
    previous = today - timedelta(days=1)
    return str(previous.day)

def get_attendance_times():
    previous_day = get_previous_day()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        try:
            context = browser.new_context(storage_state=STORAGE_FILE)
        except:
            context = browser.new_context()

        page = context.new_page()
        page.goto("https://testmaq.sharepoint.com/myspace/Pages/MySpace.aspx")

        if not page.url.startswith("https://testmaq.sharepoint.com/myspace/Pages/MySpace.aspx"):
            print("Please log in manually. Waiting for up to 2 minutes...")
            page.wait_for_url("**/myspace/Pages/MySpace.aspx", timeout=120000)
            context.storage_state(path=STORAGE_FILE)
            print("Login saved.")

        try:
            page.wait_for_selector("a:has-text('Attendance')", timeout=60000)
            page.click("a:has-text('Attendance')")
        except:
            print("Attendance tab not found.")
            context.close()
            browser.close()
            return "--:--", "--:--"

        try:
            page.wait_for_selector("ul.days", timeout=60000)
        except:
            print("Attendance calendar did not load.")
            context.close()
            browser.close()
            return "--:--", "--:--"

        max_wait = 60
        found = False
        in_time = out_time = "--:--"

        for _ in range(max_wait):
            days = page.query_selector_all("ul.days > li")
            for day in days:
                date_elem = day.query_selector("span.date")
                if date_elem and date_elem.inner_text().strip() == previous_day:
                    parent_div = day.query_selector("div > div")
                    if parent_div:
                        full_text = parent_div.inner_text().strip().split('\n')
                        in_time = full_text[0] if len(full_text) > 0 else "--:--"
                        out_time = full_text[1] if len(full_text) > 1 else "--:--"
                        found = True
                        break
            if found:
                break
            time.sleep(1)

        context.close()
        browser.close()
        return in_time, out_time

if __name__ == "__main__":
    sign_in, sign_out = get_attendance_times()
    print(f"Sign-in: {sign_in}, Sign-out: {sign_out}")

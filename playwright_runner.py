from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta

def get_previous_day():
    return str((datetime.today() - timedelta(days=2)).day)

def fetch_attendance(user_id: str, state_path: str):
    previous_day = get_previous_day()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(storage_state=state_path)
        page = context.new_page()
        page.goto("https://testmaq.sharepoint.com/myspace/Pages/MySpace.aspx")

        try:
            page.wait_for_selector("a:has-text('Attendance')", timeout=60000)
            page.click("a:has-text('Attendance')")
            page.wait_for_selector("ul.days", timeout=60000)

            days = page.query_selector_all("ul.days > li")
            for day in days:
                date_elem = day.query_selector("span.date")
                if date_elem and date_elem.inner_text().strip() == previous_day:
                    parent_div = day.query_selector("div > div")
                    if parent_div:
                        full_text = parent_div.inner_text().strip().split('\n')
                        in_time = full_text[0] if len(full_text) > 0 else '--:--'
                        out_time = full_text[1] if len(full_text) > 1 else '--:--'
                        return in_time, out_time

        except Exception as e:
            return "--:--", "--:--"

        finally:
            context.close()
            browser.close()

    return "--:--", "--:--"

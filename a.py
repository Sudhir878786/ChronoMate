from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright

from datetime import datetime, timedelta
import time

def get_previous_day():
    today = datetime.today()
    previous = today - timedelta(days=1)
    return str(previous.day)

async def get_attendance_times(state_path: str):
    from datetime import datetime, timedelta
    import time

    previous_day = (datetime.today() - timedelta(days=1)).day
    in_time, out_time = "--:--", "--:--"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(storage_state=state_path)
        except:
            context = await browser.new_context()

        page = await context.new_page()
        await page.goto("https://testmaq.sharepoint.com/myspace/Pages/MySpace.aspx")

        if not page.url.startswith("https://testmaq.sharepoint.com/myspace/Pages/MySpace.aspx"):
            print("Manual login required. Waiting...")
            try:
                await page.wait_for_url("**/myspace/Pages/MySpace.aspx", timeout=120_000)
                await context.storage_state(path=state_path)
            except:
                return in_time, out_time

        try:
            await page.click("a:has-text('Attendance')")
            await page.wait_for_selector("ul.days", timeout=60_000)
        except:
            return in_time, out_time

        days = await page.query_selector_all("ul.days > li")
        for day in days:
            date_elem = await day.query_selector("span.date")
            if date_elem:
                date_text = (await date_elem.inner_text()).strip()
                if date_text == str(previous_day):
                    parent_div = await day.query_selector("div > div")
                    if parent_div:
                        full_text = (await parent_div.inner_text()).strip().split('\n')
                        in_time = full_text[0] if len(full_text) > 0 else "--:--"
                        out_time = full_text[1] if len(full_text) > 1 else "--:--"
                    break

        await context.close()
        await browser.close()

    return in_time, out_time

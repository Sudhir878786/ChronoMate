# a.py
from playwright.async_api import async_playwright
from datetime import datetime, timedelta

def get_previous_day():
    today = datetime.today()
    previous = today - timedelta(days=1)
    return str(previous.day)

async def get_attendance_times(state_path):
    previous_day = get_previous_day()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(storage_state=state_path)
        except:
            context = await browser.new_context()

        page = await context.new_page()
        await page.goto("https://testmaq.sharepoint.com/myspace/Pages/MySpace.aspx")

        if not page.url.startswith("https://testmaq.sharepoint.com/myspace/Pages/MySpace.aspx"):
            print("Please log in manually. Waiting for up to 2 minutes...")
            await page.wait_for_url("**/myspace/Pages/MySpace.aspx", timeout=120000)
            await context.storage_state(path=state_path)
            print("Login saved.")

        try:
            await page.wait_for_selector("a:has-text('Attendance')", timeout=60000)
            await page.click("a:has-text('Attendance')")
        except:
            print("Attendance tab not found.")
            await context.close()
            await browser.close()
            return "--:--", "--:--"

        try:
            await page.wait_for_selector("ul.days", timeout=60000)
        except:
            print("Attendance calendar did not load.")
            await context.close()
            await browser.close()
            return "--:--", "--:--"

        max_wait = 60
        found = False
        in_time = out_time = "--:--"

        for _ in range(max_wait):
            days = await page.query_selector_all("ul.days > li")
            for day in days:
                date_elem = await day.query_selector("span.date")
                if date_elem:
                    date_text = (await date_elem.inner_text()).strip()
                    if date_text == previous_day:
                        parent_div = await day.query_selector("div > div")
                        if parent_div:
                            full_text = (await parent_div.inner_text()).strip().split('\n')
                            in_time = full_text[0] if len(full_text) > 0 else "--:--"
                            out_time = full_text[1] if len(full_text) > 1 else "--:--"
                            found = True
                            break
            if found:
                break
            await page.wait_for_timeout(1000)

        await context.close()
        await browser.close()
        return in_time, out_time

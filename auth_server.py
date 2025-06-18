import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from playwright.async_api import async_playwright
import uuid

app = FastAPI()
UPLOAD_DIR = "employee_states"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/login", response_class=HTMLResponse)
async def login_browser(request: Request, user_id: str):
    # This URL will be opened by the user in their own browser
    page_html = f"""
    <html>
    <head><title>Login</title></head>
    <body>
        <h2>🔐 Login for Attendance Bot</h2>
        <p>Please wait, browser login is starting...</p>
        <script>
            window.location.href = "/start?user_id={user_id}";
        </script>
    </body>
    </html>
    """
    return page_html

@app.get("/start")
async def login_start(user_id: str):
    state_path = os.path.join(UPLOAD_DIR, f"{user_id}_state.json")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://login.microsoftonline.com/")
        await page.wait_for_timeout(15000)  # Give user time to enter credentials

        try:
            await context.storage_state(path=state_path)
            await browser.close()
            return HTMLResponse(f"<h2>✅ Login successful!</h2><p>You may close this tab.</p>")
        except Exception as e:
            return HTMLResponse(f"<h2>❌ Failed to save state</h2><p>{str(e)}</p>")

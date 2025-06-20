import os
import re
import asyncio
import logging
from datetime import datetime, timedelta

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)
from playwright.async_api import async_playwright

from agent import get_attendance_times  # Ensure this is async

# --- Load Env ---
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
os.makedirs("employee_states", exist_ok=True)
STATE_DIR = "employee_states"

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="bot.log",
    filemode="a"
)
logger = logging.getLogger(__name__)

# --- Conversation States ---
EMAIL = 0

# --- Helper ---
def parse_time_string(time_str):
    match = re.match(r"(\d{1,2}):(\d{2})", time_str)
    if match:
        hour, minute = int(match.group(1)), int(match.group(2))
        return datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    return None

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Use /login to authenticate and receive attendance updates.")

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📧 Please enter your work email:")
    return EMAIL

async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text
    context.user_data['email'] = email
    await update.message.reply_text("🔐 Launching browser for login... Please complete the steps within 60 seconds.")

    user_id = str(update.effective_user.id)
    state_path = os.path.join(STATE_DIR, f"{user_id}_state.json")

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context_pw = await browser.new_context()
    page = await context_pw.new_page()

    try:
        await page.goto("https://login.microsoftonline.com/")
        await page.fill("input[name='loginfmt']", email)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(3000)

        try:
            await page.wait_for_selector("div.displaySign", timeout=10000)
            number = await page.inner_text("div.displaySign")
            await update.message.reply_text(f"📲 Enter this number `{number.strip()}` in your Authenticator app.")
        except Exception:
            await update.message.reply_text("⚠️ Authenticator prompt not detected. Please continue manually.")

        await update.message.reply_text("⏳ Waiting for approval... You have 60 seconds.")
        try:
            await page.wait_for_selector('input[id="idSIButton9"]', timeout=60000)
            await page.click('input[id="idSIButton9"]')
            await update.message.reply_text("☑️ Clicked 'Yes' to stay signed in.")
        except Exception:
            await update.message.reply_text("❌ Login timeout or 'Yes' button not found. Please try again.")
            raise Exception("Timeout waiting for approval.")

        await page.wait_for_timeout(5000)
        await context_pw.storage_state(path=state_path)

        if os.path.exists(state_path) and os.path.getsize(state_path) > 1000:
            await update.message.reply_text("✅ Login successful! Session saved.")
            await schedule_dynamic_notification(context.application, user_id, state_path)
        else:
            await update.message.reply_text("❌ Session not saved. Please try again.")
            raise Exception("Session file not written properly.")

    except Exception as e:
        logger.error(f"[LoginError] User {user_id}: {e}")
        await update.message.reply_text("❌ Login failed. Please ensure you completed the login in time and try again.")
    finally:
        await browser.close()
        await playwright.stop()
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Login cancelled.")
    return ConversationHandler.END

async def see_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    state_path = os.path.join(STATE_DIR, f"{user_id}_state.json")

    if not os.path.exists(state_path) or os.path.getsize(state_path) < 1000:
        await update.message.reply_text("❌ You need to log in again. Your session file is missing or invalid.")
        return

    await update.message.reply_text("🔍 Checking today's attendance...")
    in_time, out_time = await get_attendance_times(state_path)

    if in_time != "--:--":
        await update.message.reply_text(f"🟢 In-Time: `{in_time}`\n🔴 Out-Time: `{out_time}`", parse_mode="Markdown")
        await schedule_dynamic_notification(context.application, user_id, state_path)
    else:
        await update.message.reply_text("ℹ️ In-time not yet available. We will keep checking.")
        await schedule_dynamic_notification(context.application, user_id, state_path)

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    state_path = os.path.join(STATE_DIR, f"{user_id}_state.json")
    if os.path.exists(state_path):
        os.remove(state_path)
        await update.message.reply_text("🔓 You have been logged out. Use /login to sign in again.")
    else:
        await update.message.reply_text("ℹ️ No active session found.")

# --- Scheduler ---
async def schedule_dynamic_notification(app, user_id, state_path):
    now = datetime.now()
    first_check = now.replace(hour=12, minute=10, second=0, microsecond=0)
    if now < first_check:
        await asyncio.sleep((first_check - now).total_seconds())

    max_attempts = 6
    for attempt in range(max_attempts):
        try:
            in_time_str, _ = await get_attendance_times(state_path)
            if in_time_str != "--:--":
                in_time_dt = parse_time_string(in_time_str)
                if in_time_dt:
                    notify_time = in_time_dt + timedelta(hours=8)
                    wait_seconds = max((notify_time - datetime.now()).total_seconds(), 0)

                    async def send_later():
                        await asyncio.sleep(wait_seconds)
                        await app.bot.send_message(
                            chat_id=int(user_id),
                            text="🕗 Your 8 hours are over! Time to enjoy the evening 🎉"
                        )
                        logger.info(f"✅ Sent evening message to user {user_id}")

                    asyncio.create_task(send_later())
                    logger.info(f"⏰ Scheduled evening alert at {notify_time.strftime('%H:%M')} for user {user_id}")
                    return
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed for user {user_id}: {e}")

        await asyncio.sleep(2 * 60 * 60)

    logger.error(f"❌ Failed to find in-time after {max_attempts} attempts for user {user_id}")

# --- Entry Point ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("login", login)],
        states={EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("seeattendance", see_attendance))
    app.add_handler(CommandHandler("logout", logout))
    app.add_handler(conv_handler)

    logger.info("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

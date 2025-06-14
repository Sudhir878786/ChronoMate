from agent import get_attendance_times
import requests

# Replace with your Telegram bot token and chat ID
BOT_TOKEN = '8087115073:AAEb_80xgntmH4k2r2JutrTWDHGYCJIMEwI'
CHAT_ID = '6377327225'

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print("✅ Telegram message sent.")
    else:
        print("❌ Failed to send Telegram message:", response.text)

if __name__ == "__main__":
    sign_in, sign_out = get_attendance_times()
    message = f"🕒 Attendance Report:\nSign-in: {sign_in}\nSign-out: {sign_out}\n\n🧠 Time to shut down the laptop and enjoy your evening!"
    send_telegram_message(message)

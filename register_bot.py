from flask import Flask, request
import json
import os

app = Flask(__name__)


FILE_NAME = "user_chat_ids.json"

# Ensure file exists
if not os.path.exists(FILE_NAME):
    with open(FILE_NAME, "w") as f:
        json.dump({}, f)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        username = message["from"].get("first_name", "Unknown")

        with open(FILE_NAME, "r") as f:
            users = json.load(f)

        users[str(username)] = chat_id

        with open(FILE_NAME, "w") as f:
            json.dump(users, f, indent=2)

        # Optional: send welcome message back
        import requests
        send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": f"✅ You are now registered for AI attendance notifications, {username}!"
        }
        requests.post(send_url, data=payload)

    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000)

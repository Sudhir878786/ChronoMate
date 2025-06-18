import os
import json

STORAGE_DIR = "storage"

def get_storage_path(user_id: str):
    os.makedirs(STORAGE_DIR, exist_ok=True)
    return os.path.join(STORAGE_DIR, f"{user_id}.json")

def save_storage_state(user_id: str, path: str):
    # Can add to DB if needed, here we just save file
    print(f"Saved storage for user {user_id} at {path}")

def list_registered_users():
    return [f.split(".")[0] for f in os.listdir(STORAGE_DIR) if f.endswith(".json")]

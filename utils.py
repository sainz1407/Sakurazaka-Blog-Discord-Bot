import os
import json

LAST_FILE = "last_post.json"

def load_last_date():
    if os.path.exists(LAST_FILE):
        with open(LAST_FILE, 'r') as f:
            return json.load(f).get("last_post_date", "2000/01/01 00:00:00")
    return "2000/01/01 00:00:00"

def save_last_date(post_date):
    with open(LAST_FILE, 'w') as f:
        json.dump({"last_post_date": post_date}, f)

def get_member_channels():
    member_channels = {}
    for key, value in os.environ.items():
        if key.startswith("CHANNEL_") and value.isdigit():
            member_name = key[len("CHANNEL_"):].replace("_", " ")
            member_channels[member_name] = int(value)
    return member_channels
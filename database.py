
import json
import os
from datetime import datetime

CONFIG_FILE = "system_config.json"
DATA_FILE = "system_data.json"

DEFAULT_CONFIG = {
    "welcome_message": "🚀 <b>#name_user مرحباً بك في g5wbot</b>\n━━━━━━━━━━━━━━━━━━━━━━\n🔥 <b>نظام حقن وتوقيع التطبيقات المتقدم</b>\n━━━━━━━━━━━━━━━━━━━━━━\n🆔 معرفك: <code>#id</code>\n━━━━━━━━━━━━━━━━━━━━━━\nاختر من الخيارات أدناه:",
    "buttons": [
        {"text": "⚡ حقن وتوقيع", "callback_data": "inject_action", "type": "web_app"},
        {"text": "👑 قسم VIP", "callback_data": "vip_section", "type": "callback"},
        {"text": "💰 تبرع بالنجوم", "callback_data": "donate_stars", "type": "callback"},
        {"text": "🔗 دعوة صديق", "callback_data": "invite_friends", "type": "callback"}
    ],
    "vip_price": 99,
    "vip_description": "🌟 عضوية VIP مدى الحياة - ميزات حصرية وأولوية في الخدمة",
    "webapp_url": "https://pywahm.onrender.com",
    "invite_reward_points": 5,
    "free_attempts": 2
}

def load_json(file_path, default):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return default

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class Database:
    def __init__(self):
        self.config = load_json(CONFIG_FILE, DEFAULT_CONFIG)
        self.users = load_json(DATA_FILE, {})

    def get_user(self, user_id):
        uid = str(user_id)
        if uid not in self.users:
            self.users[uid] = {
                "user_id": int(user_id),
                "attempts": self.config.get("free_attempts", 2),
                "invites": 0,
                "points": 0,
                "is_vip": False,
                "invited_users": [],
                "total_donations": 0,
                "joined_date": datetime.now().isoformat()
            }
            self.save_users()
        return self.users[uid]

    def update_user(self, user_id, **kwargs):
        uid = str(user_id)
        if uid in self.users:
            self.users[uid].update(kwargs)
            self.save_users()

    def save_users(self):
        save_json(DATA_FILE, self.users)

    def save_config(self):
        save_json(CONFIG_FILE, self.config)

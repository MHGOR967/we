
import threading
import os
import asyncio
from app import app
from bot import run_bot

def start_flask():
    print("🌐 Starting Flask Web Server...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Start Flask in a background thread
    threading.Thread(target=start_flask, daemon=True).start()
    
    # Start Aiogram Bot in the main thread
    print("🤖 Starting Telegram Bot...")
    asyncio.run(run_bot())

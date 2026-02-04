import os
import http.server
import socketserver
import threading
import telebot
import google.generativeai as genai
import time

# =========================================================
# 0. RENDER HEALTH CHECK (THE "IMMEDIATE" VERSION)
# =========================================================
def run_health_check():
    port = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with socketserver.TCPServer(("0.0.0.0", port), handler) as httpd:
            print(f"✅ Health check server is ACTIVE on port {port}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Health check error: {e}")

# START THE WEB SERVER IMMEDIATELY
threading.Thread(target=run_health_check, daemon=True).start()

# GIVE THE SERVER 1 SECOND TO WAKE UP
time.sleep(1)

# =========================================================
# 1. SECURITY & CONFIG
# =========================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not TELEGRAM_TOKEN or not GOOGLE_API_KEY:
    print("❌ ERROR: Missing API keys!")
    exit(1)

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

print("🚀 Lead Fountain is starting up...")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_name = message.from_user.first_name
    prompt = f"User {user_name} says: {message.text}. Respond as Lead Fountain Roofing assistant."
    try:
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
    except Exception as e:
        print(f"❌ AI Error: {e}")

# =========================================================
# 2. START BOT
# =========================================================
print("📡 Bot is now polling...")
bot.infinity_polling()

import os
import http.server
import socketserver
import threading
import telebot
import google.generativeai as genai
import time
import re

# =========================================================
# 0. RENDER HEALTH CHECK & CONFIG
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

threading.Thread(target=run_health_check, daemon=True).start()
time.sleep(1)

# API KEYS
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# REPLACE THE 0 BELOW WITH YOUR CHAT ID FROM @userinfobot
MY_CHAT_ID = "1556353947" 

if not TELEGRAM_TOKEN or not GOOGLE_API_KEY:
    print("❌ ERROR: Missing API keys!")
    exit(1)

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

print("🚀 Lead Fountain Ontario Concierge is starting up...")

# =========================================================
# 1. THE BRAIN (ONTARIO MASTER PROMPT)
# =========================================================
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_name = message.from_user.first_name
    user_text = message.text
    
    print(f"📥 New message from {user_name}: {user_text}")

    # Universal High-Ticket System Prompt for Ontario
    prompt = f"""
    You are the Senior Client Concierge for 'Lead Fountain Professional Services'. 
    You represent elite local service providers across Ontario.
    
    YOUR ROLE:
    1. Act as a high-level consultant. Be professional, sophisticated, and helpful.
    2. Identify the user's specific project or problem (Roofing, Legal, HVAC, etc.).
    3. POSITIONING: Frame the service as a premium investment, not a cheap fix.
    
    QUALIFICATION GOALS:
    - Ask: "What is the scope of the project you're considering?"
    - Ask: "What part of Ontario are you located in?"
    - FINAL GOAL: Get their Name and Phone Number so a Senior Partner can provide a formal consultation.
    
    TONE: Expert, reassuring, and concise. No fluff.
    
    Context:
    User Name: {user_name}
    User Message: {user_text}
    """

    try:
        # Generate AI response
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
        
        # LEAD NOTIFICATION LOGIC
        # If the message contains 7 or more digits, it's likely a phone number
        if re.search(r'\d{7,}', user_text) and MY_CHAT_ID != "0":
            alert_text = f"🚨 NEW LEAD CAPTURED!\n\n👤 Name: {user_name}\n📍 Msg: {user_text}\n\nFollow up immediately!"
            bot.send_message(MY_CHAT_ID, alert_text)
            print(f"📢 Lead notification sent to Admin!")

    except Exception as e:
        print(f"❌ Error: {e}")
        bot.reply_to(message, "I'm reviewing your request. One of our specialists will be with you shortly. May I have your best contact number?")

# =========================================================
# 2. START
# =========================================================
print("📡 Concierge is now polling...")
bot.infinity_polling()

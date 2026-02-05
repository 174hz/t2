import os
import http.server
import socketserver
import threading
import telebot
import google.generativeai as genai
import time
import re
from collections import defaultdict

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

# YOUR SETTINGS
MY_CHAT_ID = "1556353947"
PAYMENT_URL = "https://buy.stripe.com/test_your_link_here" 

# MEMORY STORAGE (Holds last 10 messages per user)
user_history = defaultdict(list)

if not TELEGRAM_TOKEN or not GOOGLE_API_KEY:
    print("❌ ERROR: Missing API keys!")
    exit(1)

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

print("🚀 Lead Fountain Ontario Concierge is starting up...")

# =========================================================
# 1. THE BRAIN (CONTEXT-AWARE PROMPT)
# =========================================================
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    user_name = message.from_user.first_name
    user_text = message.text
    
    # 1. Update History (Store user message)
    user_history[user_id].append(f"User: {user_text}")
    if len(user_history[user_id]) > 10:
        user_history[user_id].pop(0)

    # 2. Build Contextual Prompt
    history_context = "\n".join(user_history[user_id])
    
    prompt = f"""
    You are the Senior Client Concierge for 'Lead Fountain Professional Services' in Ontario.
    
    CRITICAL INSTRUCTIONS:
    - REVIEW THE HISTORY BELOW. If the user has already provided their location, project details, or name, DO NOT ask for them again.
    - Be observant. If they say "Leaky roof in Guelph", acknowledge the urgency in Guelph immediately.
    - If you have the project info and location, pivot immediately to asking for their Name and Phone Number to schedule the "Senior Partner".
    - Avoid being repetitive. If you just asked a question, don't ask it again in a different way.

    GOALS:
    1. Identify the project scope and Ontario city.
    2. Secure a Name and Phone Number for a follow-up.
    3. Maintain an elite, professional, and efficient tone.

    CONVERSATION HISTORY:
    {history_context}
    
    Response:
    """

    try:
        # Generate AI response
        response = model.generate_content(prompt)
        bot_reply = response.text
        
        # Update History (Store bot response)
        user_history[user_id].append(f"Assistant: {bot_reply}")
        
        bot.reply_to(message, bot_reply)
        
        # 3. SMART PAYMENT BUTTON (Detects buying intent)
        buying_signals = ["quote", "price", "cost", "book", "appointment", "consultation", "pay"]
        if any(signal in user_text.lower() for signal in buying_signals):
            markup = telebot.types.InlineKeyboardMarkup()
            btn = telebot.types.InlineKeyboardButton("💳 Secure Your Consultation", url=PAYMENT_URL)
            markup.add(btn)
            bot.send_message(
                message.chat.id, 
                "To prioritize your request and secure a slot with our Senior Partner, you may use our secure portal below:", 
                reply_markup=markup
            )

        # 4. LEAD NOTIFICATION LOGIC
        if re.search(r'\d{7,}', user_text) and MY_CHAT_ID != "0":
            alert_text = f"🚨 NEW LEAD CAPTURED!\n\n👤 Name: {user_name}\n📍 Msg: {user_text}\n\nFollow up immediately!"
            bot.send_message(MY_CHAT_ID, alert_text)
            print(f"📢 Lead notification sent to Admin!")

    except Exception as e:
        print(f"❌ Error: {e}")
        bot.reply_to(message, "I am reviewing your details. Can I have your phone number to have a Senior Partner call you back?")

# =========================================================
# 2. START
# =========================================================
print("📡 Concierge is now polling...")
bot.infinity_polling()

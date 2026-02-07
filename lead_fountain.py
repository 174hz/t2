import json
import re
import google.generativeai as genai
from js import Response, fetch

# =========================================================
# 1. THE BRAIN (CONTEXT-AWARE LOGIC)
# =========================================================
async def get_ai_reply(user_text, user_id, user_name, env):
    genai.configure(api_key=env.GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')

    # 1. RETRIEVE HISTORY FROM CLOUDFLARE KV
    history_raw = await env.LEAD_HISTORY.get(str(user_id))
    history_list = json.loads(history_raw) if history_raw else []

    # 2. Update History
    history_list.append(f"User: {user_text}")
    if len(history_list) > 12:  # Keep it tight for token limits
        history_list.pop(0)
    
    history_context = "\n".join(history_list)
    
    prompt = f"""
    You are the Senior Client Concierge for 'Lead Fountain Professional Services' in Ontario.
    
    CRITICAL INSTRUCTIONS:
    - REVIEW HISTORY: If location/project/name is known, don't ask again.
    - Urgency: Acknowledge local Ontario cities (Guelph, etc.) immediately.
    - Pivot: Once scope is known, ask for Phone Number for a "Senior Partner" call.

    CONVERSATION HISTORY:
    {history_context}
    
    Response:
    """

    response = model.generate_content(prompt)
    bot_reply = response.text

    # 3. SAVE HISTORY BACK TO KV
    history_list.append(f"Assistant: {bot_reply}")
    await env.LEAD_HISTORY.put(str(user_id), json.dumps(history_list), {"expirationTtl": 3600}) # Expire after 1 hour of silence
    
    return bot_reply

# =========================================================
# 2. CLOUDFLARE HANDLER (WEBHOOK)
# =========================================================
async def on_fetch(request, env):
    # Only process POST requests from Telegram
    if request.method != "POST":
        return Response.new("System Active", status=200)

    try:
        data = await request.json()
        if "message" not in data:
            return Response.new("OK")

        message = data["message"]
        chat_id = message["chat"]["id"]
        user_text = message.get("text", "")
        user_name = message["from"].get("first_name", "Client")

        # Get AI Response
        bot_reply = await get_ai_reply(user_text, chat_id, user_name, env)

        # Telegram API Config
        tg_url = f"https://api.telegram.org/bot{env.TELEGRAM_TOKEN}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": bot_reply
        }

        # 3. SMART PAYMENT BUTTON
        buying_signals = ["quote", "price", "cost", "book", "appointment", "consultation", "pay"]
        if any(signal in user_text.lower() for signal in buying_signals):
            payload["reply_markup"] = {
                "inline_keyboard": [[
                    {"text": "💳 Secure Your Consultation", "url": env.PAYMENT_URL}
                ]]
            }

        # Send message via Fetch API
        await fetch(tg_url, {
            "method": "POST",
            "body": json.dumps(payload),
            "headers": {"Content-Type": "application/json"}
        })

        # 4. LEAD NOTIFICATION
        if re.search(r'\d{7,}', user_text):
            alert = {
                "chat_id": env.MY_CHAT_ID,
                "text": f"🚨 NEW LEAD!\n👤 Name: {user_name}\n📍 Msg: {user_text}"
            }
            await fetch(tg_url, {
                "method": "POST",
                "body": json.dumps(alert),
                "headers": {"Content-Type": "application/json"}
            })

        return Response.new("OK")

    except Exception as e:
        return Response.new(str(e), status=500)

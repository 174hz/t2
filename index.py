import json
import re
from js import Response, fetch

# Use the WorkerEntrypoint if available, or just a standard class
class Default:
    def __init__(self, env):
        self.env = env

    async def fetch(self, request):
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

            # Get AI Response via Direct Fetch
            bot_reply = await self.get_ai_reply(user_text, chat_id, user_name)

            # Telegram API Config
            tg_url = f"https://api.telegram.org/bot{self.env.TELEGRAM_TOKEN}/sendMessage"
            
            payload = {"chat_id": chat_id, "text": bot_reply}

            # Send message via Fetch API
            await fetch(tg_url, {
                "method": "POST",
                "body": json.dumps(payload),
                "headers": {"Content-Type": "application/json"}
            })

            # Lead Notification for Phone Numbers
            if re.search(r'\d{7,}', user_text):
                alert = {
                    "chat_id": self.env.MY_CHAT_ID,
                    "text": f"🚨 NEW LEAD!\n👤 {user_name}\n📍 {user_text}"
                }
                await fetch(tg_url, {
                    "method": "POST",
                    "body": json.dumps(alert),
                    "headers": {"Content-Type": "application/json"}
                })

            return Response.new("OK")

        except Exception as e:
            return Response.new(f"Error: {str(e)}", status=200)

    async def get_ai_reply(self, user_text, user_id, user_name):
        # 1. RETRIEVE HISTORY FROM KV
        history_raw = await self.env.LEAD_HISTORY.get(str(user_id))
        history_list = json.loads(history_raw) if history_raw else []
        history_list.append(f"User: {user_text}")
        
        if len(history_list) > 10:
            history_list.pop(0)
        
        history_context = "\n".join(history_list)
        prompt = f"System: You are the Senior Client Concierge for Lead Fountain. Current Conversation:\n{history_context}\nAssistant:"

        # 2. DIRECT GEMINI FETCH
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.env.GOOGLE_API_KEY}"
        
        resp = await fetch(gemini_url, {
            "method": "POST",
            "body": json.dumps({"contents": [{"parts": [{"text": prompt}]}]}),
            "headers": {"Content-Type": "application/json"}
        })
        
        res_data = await resp.json()
        bot_reply = res_data['candidates'][0]['content']['parts'][0]['text']

        # 3. SAVE HISTORY
        history_list.append(f"Assistant: {bot_reply}")
        await self.env.LEAD_HISTORY.put(str(user_id), json.dumps(history_list), {"expirationTtl": 3600})
        
        return bot_reply

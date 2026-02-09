from workers import Response, WorkerEntrypoint, fetch
import json
import re

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "GET":
            return Response("Lead-Fountain: Online and Secured.")

        try:
            body = await request.json()
            if "message" not in body: return Response("OK")
            
            chat_id = str(body["message"]["chat"]["id"])
            user_text = body["message"].get("text", "")
            
            # --- CONFIG ---
            # Use the variables exactly as named below
            api_key = "PASTE_YOUR_AIza_KEY_HERE" 
            tg_token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"
            my_admin_id = "1556353947" 

            # --- 1. MEMORY ---
            kv = getattr(self.env, "LEAD_HISTORY", None)
            history = ""
            if kv:
                history = await kv.get(chat_id) or ""
            context = f"{history}\nUser: {user_text}"

            # --- 2. AI BRAIN ---
            system_prompt = (
                "You are the AI Assistant for Lead-Fountain. Collect: Full Name, Phone, "
                "Scope (Repair/Replace), and Best Time to Call. Be professional."
            )
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": f"{system_prompt}\n\nHistory: {context}"}]}]}

            ai_res = await fetch(url, method="POST", body=json.dumps(payload))
            ai_data = await ai_res.json()
            
            # Extract AI reply safely
            if 'candidates' in ai_data:
                bot_reply = ai_data['candidates'][0]['content']['parts'][0]['text']
            else:
                bot_reply = "Thanks for that. What is the best phone number to reach you at?"

            # --- 3. SMART ALERT (To You) ---
            # If a phone number is detected, send a private alert to your ID
            if re.search(r'\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}', user_text):
                alert_text = f"💰 **NEW LEAD!** 💰\n\n**Details:** {user_text}\n\n**History:** {history}"
                await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    method="POST", headers={"Content-Type": "application/json"},
                    body=json.dumps({"chat_id": my_admin_id, "text": alert_text}))

            # --- 4. SAVE & REPLY (To Customer) ---
            if kv:
                await kv.put(chat_id, f"{context}\nAI: {bot_reply}"[-2000:])

            await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                method="POST", headers={"Content-Type": "application/json"},
                body=json.dumps({"chat_id": chat_id, "text": bot_reply}))

            return Response("OK", status=200)
            
        except Exception as e:
            # Silently catch errors so the bot stays 'alive' in Telegram's eyes
            return Response("OK", status=200)

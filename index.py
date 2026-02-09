from workers import Response, WorkerEntrypoint, fetch
import json
import re

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "GET": return Response("Lead-Fountain: Online.")

        try:
            body = await request.json()
            if "message" not in body: return Response("OK")
            
            chat_id = str(body["message"]["chat"]["id"])
            user_text = body["message"].get("text", "")
            
            # --- CONFIG ---
            # IMPORTANT: Check that 'GOOGLE_API_KEY' is the EXACT name in Cloudflare Settings
            api_key = getattr(self.env, "GOOGLE_API_KEY", None)
            tg_token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"
            my_admin_id = "1556353947" 

            # --- 1. MEMORY ---
            kv = getattr(self.env, "LEAD_HISTORY", None)
            history = await kv.get(chat_id) or "" if kv else ""
            context = f"{history}\nUser: {user_text}"

            # --- 2. AI CALL ---
            bot_reply = ""
            if api_key:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
                payload = {"contents": [{"parts": [{"text": f"You are a roofing lead bot. Collect Name, Phone, Location, and Scope. History: {context}"}]}]}
                
                ai_res = await fetch(url, method="POST", body=json.dumps(payload))
                ai_data = await ai_res.json()
                
                if 'candidates' in ai_data:
                    bot_reply = ai_data['candidates'][0]['content']['parts'][0]['text']
                else:
                    # This tells us if the API Key is invalid or empty
                    bot_reply = f"System Note: AI Error - {json.dumps(ai_data)[:100]}"
            else:
                bot_reply = "System Note: GOOGLE_API_KEY not found in Cloudflare Variables."

            # --- 3. ALERT (ONLY TO YOU) ---
            if re.search(r'\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}', user_text):
                alert_text = f"💰 **NEW LEAD** 💰\n\n**User:** {user_text}\n\n**History:** {history[-200:]}"
                await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    method="POST", headers={"Content-Type": "application/json"},
                    body=json.dumps({"chat_id": my_admin_id, "text": alert_text}))

            # --- 4. REPLY (ONLY TO CUSTOMER) ---
            # If the chat is NOT the admin, OR if it's the admin doing a test, send the AI reply
            if chat_id != my_admin_id or "Ajax" in user_text:
                # If the bot_reply is still empty, use a polite backup
                final_text = bot_reply if bot_reply else "Thanks! What's the best time to call you?"
                await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    method="POST", headers={"Content-Type": "application/json"},
                    body=json.dumps({"chat_id": chat_id, "text": final_text}))

            # --- 5. SAVE ---
            if kv:
                await kv.put(chat_id, f"{context}\nAI: {bot_reply}"[-1000:])

            return Response("OK", status=200)
            
        except Exception as e:
            return Response("OK", status=200)

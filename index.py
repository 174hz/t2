from workers import Response, WorkerEntrypoint, fetch
import json
import re

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "GET": return Response("Lead-Fountain: Live.")

        try:
            body = await request.json()
            if "message" not in body: return Response("OK")
            
            chat_id = str(body["message"]["chat"]["id"])
            user_text = body["message"].get("text", "")
            
            # --- CONFIG ---
            api_key = "PASTE_YOUR_AIza_KEY_HERE" 
            tg_token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"
            my_admin_id = "1556353947" # Using the ID from your last message

            # --- 1. MEMORY ---
            kv = getattr(self.env, "LEAD_HISTORY", None)
            history = await kv.get(chat_id) or "" if kv else ""
            context = f"{history}\nUser: {user_text}"

            # --- 2. AI BRAIN ---
            system_prompt = (
                "You are the AI Assistant for Lead-Fountain. The user is asking about roofing. "
                "Confirm you have their details. If they gave a phone number and time, "
                "say: 'Got it! A specialist will call you at that time.' Be very brief."
            )
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": f"{system_prompt}\n\nChat History:\n{context}"}]}]}

            ai_res = await fetch(url, method="POST", body=json.dumps(payload))
            ai_data = await ai_res.json()
            
            # Get AI reply or use a polite fallback
            try:
                bot_reply = ai_data['candidates'][0]['content']['parts'][0]['text']
            except:
                bot_reply = "Got it! I've passed your details to our Richmond Hill specialist. They will call you shortly."

            # --- 3. SMART ALERT (ONLY TO YOU) ---
            if re.search(r'\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}', user_text):
                alert_text = f"💰 **NEW LEAD CAPTURED** 💰\n\n**Info:** {user_text}\n\n**Chat:** {chat_id}"
                # Send to ADMIN (You)
                await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    method="POST", headers={"Content-Type": "application/json"},
                    body=json.dumps({"chat_id": my_admin_id, "text": alert_text}))

            # --- 4. REPLY (ONLY TO CUSTOMER) ---
            # If the current user IS the admin, don't send the customer reply to avoid double messages
            if chat_id != my_admin_id or " Richmond Hill" in user_text:
                await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    method="POST", headers={"Content-Type": "application/json"},
                    body=json.dumps({"chat_id": chat_id, "text": bot_reply}))

            # --- 5. SAVE ---
            if kv:
                await kv.put(chat_id, f"{context}\nAI: {bot_reply}"[-1500:])

            return Response("OK", status=200)
            
        except Exception:
            return Response("OK", status=200)

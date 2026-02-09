from workers import Response, WorkerEntrypoint, fetch
import json
import re

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "GET": return Response("Lead-Fountain: Secure Vault Active.")

        try:
            body = await request.json()
            if "message" not in body: return Response("OK")
            
            chat_id = str(body["message"]["chat"]["id"])
            user_text = body["message"].get("text", "")
            
            # --- SECURE CONFIG ---
            # We are pulling these from your Cloudflare Environment Variables!
            api_key = self.env.GOOGLE_API_KEY 
            tg_token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"
            my_admin_id = "1556353947" 

            # --- 1. MEMORY ---
            kv = getattr(self.env, "LEAD_HISTORY", None)
            history = await kv.get(chat_id) or "" if kv else ""
            context = f"{history}\nUser: {user_text}"

            # --- 2. THE QUALIFIER BRAIN ---
            system_prompt = (
                "You are the Lead-Fountain Intake Bot. You MUST collect:\n"
                "1. Full Name, 2. Phone, 3. Location, 4. Job Scope (Repair/Replace),\n"
                "5. Job Detail (Age of roof/leaks), 6. Best Time to Call.\n\n"
                "Check History. Ask for missing info one by one. Do not confirm a call until you have Name, Phone, and Scope."
            )
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": f"{system_prompt}\n\nChat History:\n{context}"}]}]}

            ai_res = await fetch(url, method="POST", body=json.dumps(payload))
            ai_data = await ai_res.json()
            
            try:
                bot_reply = ai_data['candidates'][0]['content']['parts'][0]['text']
            except:
                bot_reply = "Got it. To help our specialist, what is your phone number and the best time to call?"

            # --- 3. SMART ALERT (TO YOU ONLY) ---
            if re.search(r'\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}', user_text):
                alert_text = f"💰 **NEW QUALIFIED LEAD** 💰\n\n**Latest:** {user_text}\n\n**History:** {history}"
                await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    method="POST", headers={"Content-Type": "application/json"},
                    body=json.dumps({"chat_id": my_admin_id, "text": alert_text}))

            # --- 4. REPLY TO CUSTOMER ---
            await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                method="POST", headers={"Content-Type": "application/json"},
                body=json.dumps({"chat_id": chat_id, "text": bot_reply}))

            # --- 5. SAVE ---
            if kv:
                await kv.put(chat_id, f"{context}\nAI: {bot_reply}"[-1500:])

            return Response("OK", status=200)
        except Exception:
            return Response("OK", status=200)

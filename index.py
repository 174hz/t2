from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "GET": return Response("Lead-Fountain: Alert System Active.")

        try:
            body = await request.json()
            if "message" not in body: return Response("OK")
            
            chat_id = str(body["message"]["chat"]["id"])
            user_text = body["message"].get("text", "")
            
            # --- CONFIG ---
            api_key = self.env.GOOGLE_API_KEY
            tg_token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"
            my_admin_id = "PASTE_YOUR_PERSONAL_ID_HERE" # Put your ID here

            # --- 1. MEMORY ---
            kv = getattr(self.env, "LEAD_HISTORY", None)
            history = await kv.get(chat_id) or "" if kv else ""
            context = f"{history}\nUser: {user_text}"

            # --- 2. AI CALL ---
            system_prompt = (
                "You are the AI Assistant for Lead-Fountain. Collect: Full Name, Phone, "
                "Scope (Repair/Replace), and Best Time to Call. "
                "Once you have ALL 4 pieces of info, tell them 'A specialist will call you shortly.' "
                "Be brief and professional."
            )
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": f"{system_prompt}\n\nHistory: {context}"}]}]}

            ai_res = await fetch(url, method="POST", body=json.dumps(payload))
            ai_data = await ai_res.json()
            bot_reply = ai_data['candidates'][0]['content']['parts'][0]['text']

            # --- 3. LEAD DETECTION & ALERT ---
            # If the AI says the 'specialist' line, it means the lead is complete!
            if "specialist will call" in bot_reply.lower():
                alert_text = f"🚨 **NEW LEAD ALERT** 🚨\n\nFull History:\n{context}\n\nGo get 'em!"
                await fetch(
                    f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    method="POST",
                    headers={"Content-Type": "application/json"},
                    body=json.dumps({"chat_id": my_admin_id, "text": alert_text})
                )

            # --- 4. SAVE & REPLY ---
            if kv:
                await kv.put(chat_id, f"{context}\nAI: {bot_reply}"[-2000:])

            await fetch(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                method="POST",
                headers={"Content-Type": "application/json"},
                body=json.dumps({"chat_id": chat_id, "text": bot_reply})
            )

            return Response("OK", status=200)
            
        except Exception:
            return Response("OK", status=200)

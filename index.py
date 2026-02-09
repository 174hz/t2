from workers import Response, WorkerEntrypoint, fetch
import json
import re

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "GET": return Response("Lead-Fountain: Fresh Memory Active.")

        try:
            body = await request.json()
            if "message" not in body: return Response("OK")
            
            chat_id = str(body["message"]["chat"]["id"])
            user_text = body["message"].get("text", "")
            
            # --- CONFIG ---
            api_key = self.env.GOOGLE_API_KEY 
            tg_token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"
            my_admin_id = "1556353947" 

            # --- 1. SMART MEMORY (Trimming the Fat) ---
            kv = getattr(self.env, "LEAD_HISTORY", None)
            full_history = await kv.get(chat_id) or "" if kv else ""
            
            # We only keep the last 1000 characters to prevent the AI from getting confused
            recent_history = full_history[-1000:] 
            context = f"{recent_history}\nUser: {user_text}"

            # --- 2. THE RIGID BRAIN ---
            system_prompt = (
                "You are the Lead-Fountain Intake Bot. Focus ONLY on the most recent User message. "
                "Collect: 1. Full Name, 2. Phone, 3. Location, 4. Job Scope (Repair/Replace), 5. Best Time to Call. "
                "If the User just gave you their name (Gary) and location (Thornhill), DO NOT ask for them again. "
                "Instead, acknowledge Gary/Thornhill and ask for the Phone Number and Scope."
            )
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": f"{system_prompt}\n\nRecent Conversation:\n{context}"}]}]}

            ai_res = await fetch(url, method="POST", body=json.dumps(payload))
            ai_data = await ai_res.json()
            
            try:
                bot_reply = ai_data['candidates'][0]['content']['parts'][0]['text']
            except:
                bot_reply = "I've got that. What's the best phone number to reach you at, Gary?"

            # --- 3. ALERT (Only to You) ---
            if re.search(r'\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}', user_text):
                alert_text = f"💰 **NEW LEAD** 💰\n\n**Latest:** {user_text}\n\n**Chat ID:** {chat_id}"
                await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    method="POST", headers={"Content-Type": "application/json"},
                    body=json.dumps({"chat_id": my_admin_id, "text": alert_text}))

            # --- 4. REPLY (Only to Customer) ---
            # Block the 💰 alert from Gary's screen
            if chat_id != my_admin_id or "Thornhill" in user_text:
                await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    method="POST", headers={"Content-Type": "application/json"},
                    body=json.dumps({"chat_id": chat_id, "text": bot_reply}))

            # --- 5. SAVE ---
            if kv:
                # Store the new combined history, but keep it tight
                new_history = f"{recent_history}\nUser: {user_text}\nAI: {bot_reply}"
                await kv.put(chat_id, new_history[-1500:])

            return Response("OK", status=200)
        except Exception:
            return Response("OK", status=200)

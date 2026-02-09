from workers import Response, WorkerEntrypoint, fetch
import json
import re

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "GET": return Response("Lead-Fountain: Status Active.")

        try:
            body = await request.json()
            if "message" not in body: return Response("OK")
            
            chat_id = str(body["message"]["chat"]["id"])
            user_text = body["message"].get("text", "")
            
            # --- CONFIG ---
            # Make sure these names match your Cloudflare Variables exactly!
            api_key = self.env.GOOGLE_API_KEY 
            tg_token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"
            my_admin_id = "1556353947" 

            # --- 1. MEMORY CHECK ---
            history = ""
            try:
                kv = getattr(self.env, "LEAD_HISTORY", None)
                if kv:
                    history = await kv.get(chat_id) or ""
                    history = history[-800:] # Keep only the very recent stuff
            except:
                history = "" # Skip memory if KV is broken

            context = f"{history}\nUser: {user_text}"

            # --- 2. AI CALL ---
            system_prompt = (
                "You are the Lead-Fountain Intake Bot. Collect: Name, Phone, Location, Job Scope. "
                "Keep it brief. If info is missing, ask for it."
            )
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": f"{system_prompt}\n\nContext: {context}"}]}]}

            ai_res = await fetch(url, method="POST", body=json.dumps(payload))
            ai_data = await ai_res.json()
            
            # Extract the AI's words
            if 'candidates' in ai_data:
                bot_reply = ai_data['candidates'][0]['content']['parts'][0]['text']
            else:
                bot_reply = "I've received your message. What is the best phone number to reach you at?"

            # --- 3. ALERT (ONLY TO YOU) ---
            if re.search(r'\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}', user_text):
                alert_payload = {"chat_id": my_admin_id, "text": f"💰 **LEAD:** {user_text}"}
                await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                            method="POST", headers={"Content-Type": "application/json"},
                            body=json.dumps(alert_payload))

            # --- 4. REPLY TO CUSTOMER ---
            await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                method="POST", headers={"Content-Type": "application/json"},
                body=json.dumps({"chat_id": chat_id, "text": bot_reply}))

            # --- 5. SAVE NEW HISTORY ---
            try:
                if kv:
                    new_mem = f"{history}\nUser: {user_text}\nAI: {bot_reply}"
                    await kv.put(chat_id, new_mem[-1000:])
            except:
                pass

            return Response("OK", status=200)

        except Exception as e:
            # This is the 'Panic' reply so you know exactly what broke
            return Response(f"Error: {str(e)}", status=200)

from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # Health Check
        if request.method == "GET":
            return Response("Lead-Fountain Engine: Online and Listening.")

        try:
            body = await request.json()
            if "message" not in body: return Response("OK")
            
            chat_id = str(body["message"]["chat"]["id"])
            user_text = body["message"].get("text", "")
            
            # --- CONFIG (Verify these one last time!) ---
            api_key = "AIzaSyBI639cobspNH8ptx9z2HQKRVyZJ7Yl9xQ" 
            tg_token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"

            # --- 1. MEMORY CHECK ---
            history = ""
            try:
                # Use getattr to safely check for the database
                kv = getattr(self.env, "LEAD_HISTORY", None)
                if kv:
                    history = await kv.get(chat_id) or ""
            except:
                pass

            # --- 2. AI BRAIN ---
            system_prompt = (
                "You are the AI Assistant for Lead-Fountain. Be professional. "
                "Collect: Full Name, Phone Number, Scope (Repair vs Replace), and Best Time to Call. "
                "Acknowledge what they already said. Ask for what is missing."
            )
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": f"{system_prompt}\n\nHistory: {history}\nUser: {user_text}"}]}]
            }

            ai_res = await fetch(url, method="POST", body=json.dumps(payload))
            ai_data = await ai_res.json()
            
            # Extract reply safely
            try:
                bot_reply = ai_data['candidates'][0]['content']['parts'][0]['text']
            except:
                bot_reply = "I'm processing your request. Could you please repeat your last detail?"

            # --- 3. UPDATE MEMORY ---
            try:
                if kv:
                    new_history = f"{history}\nUser: {user_text}\nAI: {bot_reply}"
                    # We only keep the last bit of history to avoid hitting limits
                    await kv.put(chat_id, new_history[-2000:])
            except:
                pass

            # --- 4. TELEGRAM REPLY ---
            await fetch(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                method="POST",
                headers={"Content-Type": "application/json"},
                body=json.dumps({"chat_id": chat_id, "text": bot_reply})
            )

            return Response("OK", status=200)
            
        except Exception as e:
            # If everything else fails, we don't return an error to Telegram 
            # so it doesn't keep retrying the broken message.
            return Response("OK", status=200)

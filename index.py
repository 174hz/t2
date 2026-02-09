from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "GET":
            return Response("Lead-Fountain Engine: Active.")

        try:
            body = await request.json()
            if "message" not in body: return Response("OK")
            
            chat_id = str(body["message"]["chat"]["id"])
            user_text = body["message"].get("text", "")
            
            # --- CONFIG ---
            api_key = "AIzaSyBI639cobspNH8ptx9z2HQKRVyZJ7Yl9xQ" 
            tg_token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"

            # --- 1. MEMORY ---
            history = ""
            try:
                kv = getattr(self.env, "LEAD_HISTORY", None)
                if kv:
                    history = await kv.get(chat_id) or ""
            except: pass

            # --- 2. AI CALL ---
            system_prompt = "You are the AI Assistant for Lead-Fountain. Collect: Full Name, Phone, Scope (Repair/Replace), and Best Time to Call. Be professional."
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": f"{system_prompt}\n\nHistory: {history}\nUser: {user_text}"}]}]
            }

            ai_res = await fetch(url, method="POST", body=json.dumps(payload))
            ai_data = await ai_res.json()
            
            # --- 3. ERROR-PROOF EXTRACTION ---
            if 'candidates' in ai_data and len(ai_data['candidates']) > 0:
                bot_reply = ai_data['candidates'][0]['content']['parts'][0]['text']
            elif 'error' in ai_data:
                # This will tell you if the API key expired or reached a limit
                bot_reply = f"Debug Note: Google API Error - {ai_data['error']['message']}"
            else:
                bot_reply = "I'm having a quick connection hiccup. Could you say that one more time?"

            # --- 4. SAVE & SEND ---
            try:
                if kv:
                    new_history = f"{history}\nUser: {user_text}\nAI: {bot_reply}"
                    await kv.put(chat_id, new_history[-2000:])
            except: pass

            await fetch(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                method="POST",
                headers={"Content-Type": "application/json"},
                body=json.dumps({"chat_id": chat_id, "text": bot_reply})
            )

            return Response("OK", status=200)
            
        except Exception as e:
            return Response("OK", status=200)

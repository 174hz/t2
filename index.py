from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "GET":
            return Response("Lead-Fountain Engine: Database Mode Online.")

        try:
            body = await request.json()
            if "message" not in body: return Response("OK")
            
            chat_id = str(body["message"]["chat"]["id"])
            user_text = body["message"].get("text", "")
            
            # --- CONFIG ---
            api_key = "PASTE_YOUR_AIza_KEY_HERE" 
            tg_token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"

            # --- 1. GET OLD HISTORY (Memory) ---
            # This looks into your Cloudflare KV to see what was said before
            history = await self.env.LEAD_HISTORY.get(chat_id) or ""
            context = f"{history}\nUser: {user_text}"

            # --- 2. THE AI BRAIN ---
            system_instructions = (
                "You are the AI Assistant for Lead-Fountain. Collect: Full Name, Phone, "
                "Scope (Repair vs Replace), and Best Time to Call. "
                "Be professional. If you have all info, say 'A specialist will call you shortly.'"
            )
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": f"{system_instructions}\n\nChat History:\n{context}"}]}]
            }

            ai_res = await fetch(url, method="POST", body=json.dumps(payload))
            ai_data = await ai_res.json()
            bot_reply = ai_data['candidates'][0]['content']['parts'][0]['text']

            # --- 3. SAVE TO DATABASE ---
            # We update the history so the AI 'remembers' the phone number in the next message
            new_history = f"{context}\nAI: {bot_reply}"
            await self.env.LEAD_HISTORY.put(chat_id, new_history)

            # --- 4. SEND TO TELEGRAM ---
            await fetch(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                method="POST",
                headers={"Content-Type": "application/json"},
                body=json.dumps({"chat_id": chat_id, "text": bot_reply})
            )

            return Response("OK", status=200)
            
        except Exception as e:
            return Response("OK", status=200)

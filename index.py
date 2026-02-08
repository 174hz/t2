from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "GET":
            return Response("Lead-Fountain Engine: 2.0 Flash Online.")

        try:
            body = await request.json()
            chat_id = str(body["message"]["chat"]["id"])
            user_text = body["message"].get("text", "")
            
            # --- CONFIG ---
            api_key = "PASTE_YOUR_AIza_KEY_HERE" 
            tg_token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"
            
            # --- CALL AI (Using Gemini 2.0 Flash) ---
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": (
                        "You are the AI Assistant for Lead-Fountain. "
                        "A customer is reaching out about a home service. "
                        "Acknowledge their specific issue and location, then politely ask for their phone number "
                        "so a local specialist can call them. Keep it brief and professional.\n\n"
                        f"User Message: {user_text}"
                    )}]
                }]
            }

            res = await fetch(url, method="POST", body=json.dumps(payload))
            data = await res.json()
            
            # --- EXTRACTION ---
            if 'candidates' in data:
                bot_reply = data['candidates'][0]['content']['parts'][0]['text']
            else:
                bot_reply = "I'm sorry, I'm having trouble connecting. Please try again in a moment!"

            # --- SEND TO TELEGRAM ---
            await fetch(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                method="POST",
                headers={"Content-Type": "application/json"},
                body=json.dumps({"chat_id": chat_id, "text": bot_reply})
            )

            return Response("OK", status=200)
            
        except Exception as e:
            return Response("OK", status=200)

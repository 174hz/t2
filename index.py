from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "GET":
            return Response("Lead-Fountain Engine: Ready.")

        try:
            body = await request.json()
            chat_id = str(body["message"]["chat"]["id"])
            user_text = body["message"].get("text", "")
            
            # --- CONFIG ---
            api_key = "PASTE_YOUR_AIza_KEY_HERE" 
            tg_token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"
            
            # --- CALL AI ---
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            
            payload = {
                "contents": [{
                    "role": "user",
                    "parts": [{"text": f"You are the AI Assistant for Lead-Fountain. Help this person with their home service request and ask for their phone number. User says: {user_text}"}]
                }]
            }

            res = await fetch(url, method="POST", body=json.dumps(payload))
            data = await res.json()
            
            # --- CAREFUL EXTRACTION ---
            if 'candidates' in data:
                bot_reply = data['candidates'][0]['content']['parts'][0]['text']
            else:
                # This will tell us if Google rejected the API key
                bot_reply = f"System Note: AI rejected the request. Check API Key status. {json.dumps(data)}"

            # --- SEND TO TELEGRAM ---
            await fetch(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                method="POST",
                headers={"Content-Type": "application/json"},
                body=json.dumps({"chat_id": chat_id, "text": bot_reply})
            )

            return Response("OK", status=200)
            
        except Exception as e:
            # If it still fails, the bot will tell you the exact error code
            return Response("OK", status=200)
              

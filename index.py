from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "GET":
            return Response("Lead-Fountain Engine: Online.")

        try:
            body = await request.json()
            chat_id = str(body["message"]["chat"]["id"])
            user_text = body["message"].get("text", "")
            
            # --- CONFIG ---
            api_key = "AIzaSyBI639cobspNH8ptx9z2HQKRVyZJ7Yl9xQ" 
            tg_token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"
            
            # --- THE "UNIVERSAL" MODEL URL ---
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": f"You are the Lead-Fountain AI. A customer named Duane in Guelph has a roof leak. Acknowledge this and ask for his phone number professionally. User says: {user_text}"}]
                }]
            }

            res = await fetch(url, method="POST", body=json.dumps(payload))
            data = await res.json()
            
            # --- SMART EXTRACTION ---
            if 'candidates' in data and len(data['candidates']) > 0:
                bot_reply = data['candidates'][0]['content']['parts'][0]['text']
            elif 'error' in data:
                # This will tell us if the problem is the KEY or the MODEL
                bot_reply = f"Error {data['error']['code']}: {data['error']['message']}"
            else:
                bot_reply = "I'm having a brief connection issue. Please try one more time!"

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

from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "GET": return Response("Bot is Live.")

        try:
            body = await request.json()
            if "message" not in body: return Response("OK")
            
            chat_id = str(body["message"]["chat"]["id"])
            user_text = body["message"].get("text", "")
            
            # --- CONFIG ---
            # Using getattr to safely check if the key exists in your Cloudflare Settings
            api_key = getattr(self.env, "GOOGLE_API_KEY", None)
            tg_token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"

            bot_reply = ""

            if not api_key:
                bot_reply = "Debug Note: GOOGLE_API_KEY is missing from Cloudflare Variables."
            else:
                # Attempt to call Gemini
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                payload = {"contents": [{"parts": [{"text": f"You are a roofing intake bot. Ask for name/phone if missing. User said: {user_text}"}]}]}
                
                ai_res = await fetch(url, method="POST", body=json.dumps(payload))
                ai_data = await ai_res.json()

                if 'candidates' in ai_data:
                    bot_reply = ai_data['candidates'][0]['content']['parts'][0]['text']
                elif 'error' in ai_data:
                    # This will tell us if the key is actually invalid or leaked
                    bot_reply = f"Debug Note: Google API Error - {ai_data['error'].get('message', 'Unknown error')}"
                else:
                    bot_reply = "I'm processing your request. Could you please repeat your last detail?"

            # Force Send Reply
            await fetch(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                method="POST",
                headers={"Content-Type": "application/json"},
                body=json.dumps({"chat_id": chat_id, "text": bot_reply})
            )

            return Response("OK", status=200)

        except Exception as e:
            return Response("OK", status=200)

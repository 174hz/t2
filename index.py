from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # Health Check: Visit your worker URL in a browser. 
        # If you don't see "Bot is Live", the worker isn't deployed!
        if request.method == "GET": return Response("Bot is Live.")

        try:
            body = await request.json()
            if "message" not in body: return Response("OK")
            
            chat_id = str(body["message"]["chat"]["id"])
            user_text = body["message"].get("text", "")
            
            # --- CONFIG ---
            # Double-check these match your Cloudflare 'Variables' exactly!
            api_key = getattr(self.env, "GOOGLE_API_KEY", None)
            tg_token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"
            my_admin_id = "1556353947" 

            # 1. Simple AI Logic (No KV for now to prevent crashes)
            reply = "I'm processing your request. Could you please repeat your last detail?"
            
            if api_key:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
                payload = {"contents": [{"parts": [{"text": f"User says: {user_text}. Ask for their name and phone if missing."}]}]}
                res = await fetch(url, method="POST", body=json.dumps(payload))
                data = await res.json()
                if 'candidates' in data:
                    reply = data['candidates'][0]['content']['parts'][0]['text']

            # 2. Force Send Reply to Telegram
            await fetch(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                method="POST",
                headers={"Content-Type": "application/json"},
                body=json.dumps({"chat_id": chat_id, "text": reply})
            )

            return Response("OK", status=200)

        except Exception as e:
            # If it fails, this will show up in your Cloudflare Logs
            return Response("OK", status=200)

from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # 1. WEBSITE VIEW (Check this to see if code is live)
        if request.method == "GET":
            return Response("<h1>Lead Fountain</h1><p>AI is thinking...</p>", 
                            headers={"Content-Type": "text/html"})

        # 2. BOT LOGIC
        try:
            body = await request.json()
            if "message" not in body:
                return Response("OK")

            chat_id = body["message"]["chat"]["id"]
            user_text = body["message"].get("text", "")
            
            # --- ATTEMPT GEMINI AI ---
            bot_reply = "The AI is currently calibrating. How can I help you?" # Default fallback
            
            try:
                ai_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.env.GOOGLE_API_KEY}"
                
                ai_payload = {
                    "contents": [{"parts": [{"text": f"You are a helpful concierge. Short answer: {user_text}"}]}]
                }

                ai_res = await fetch(ai_url, {
                    "method": "POST",
                    "body": json.dumps(ai_payload),
                    "headers": {"Content-Type": "application/json"}
                })
                
                ai_data = await ai_res.json()
                # Safely dig through the AI's response structure
                if 'candidates' in ai_data:
                    bot_reply = ai_data['candidates'][0]['content']['parts'][0]['text']
            except Exception as ai_err:
                # If AI fails, we just use the fallback text instead of crashing
                bot_reply = f"Concierge is online, but AI had a hiccup: {str(ai_err)}"

            # --- SEND REPLY TO USER ---
            tg_url = f"https://api.telegram.org/bot{self.env.TELEGRAM_TOKEN}/sendMessage"
            await fetch(tg_url, {
                "method": "POST",
                "body": json.dumps({"chat_id": chat_id, "text": bot_reply}),
                "headers": {"Content-Type": "application/json"}
            })

            return Response("OK")

        except Exception as e:
            # If the whole thing fails, we return OK so Telegram stops retrying
            return Response("OK")

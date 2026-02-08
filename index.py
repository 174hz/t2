from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # 1. WEBSITE STATUS
        if request.method == "GET":
            return Response("<h1>Lead Fountain</h1><p>AI Concierge is Online and Intelligent.</p>", 
                            headers={"Content-Type": "text/html"})

        # 2. AI BOT LOGIC
        try:
            body = await request.json()
            if "message" not in body:
                return Response("OK")

            chat_id = body["message"]["chat"]["id"]
            user_text = body["message"].get("text", "Hello")
            
            # --- CALL GEMINI AI ---
            ai_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.env.GOOGLE_API_KEY}"
            
            ai_payload = {
                "contents": [{
                    "parts": [{"text": f"You are the Lead Fountain Senior Concierge. Be professional, helpful, and concise. Respond to: {user_text}"}]
                }]
            }

            ai_res = await fetch(ai_url, {
                "method": "POST",
                "body": json.dumps(ai_payload),
                "headers": {"Content-Type": "application/json"}
            })
            
            ai_data = await ai_res.json()
            
            # Extract AI text
            try:
                bot_reply = ai_data['candidates'][0]['content']['parts'][0]['text']
            except:
                bot_reply = "I'm here, but I'm having a brief moment of reflection. How can I help you manually?"

            # --- SEND REPLY ---
            await fetch(f"https://api.telegram.org/bot{self.env.TELEGRAM_TOKEN}/sendMessage", {
                "method": "POST",
                "body": json.dumps({"chat_id": chat_id, "text": bot_reply}),
                "headers": {"Content-Type": "application/json"}
            })

            return Response("OK")

        except Exception as e:
            # If AI fails, the bot still says something
            return Response("OK")

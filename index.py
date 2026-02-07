from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # 1. THE WEBSITE (GET)
        if request.method == "GET":
            return Response("<h1>Lead Fountain</h1><p>Senior Client Concierge is Online.</p>", 
                            headers={"Content-Type": "text/html"})

        # 2. THE BOT (POST)
        try:
            body = await request.json()
            if "message" not in body:
                return Response("OK")

            chat_id = body["message"]["chat"]["id"]
            user_text = body["message"].get("text", "")

            # ACCESS THE TOKEN
            token = self.env.TELEGRAM_TOKEN
            
            # THE REPLY LOGIC
            # Note: We must explicitly use 'body' as a keyword argument here
            await fetch(
                f"https://api.telegram.org/bot{token}/sendMessage",
                method="POST",
                headers={"Content-Type": "application/json"},
                body=json.dumps({
                    "chat_id": chat_id,
                    "text": "The Lead Fountain Concierge is officially connected to your Telegram! How can I assist you today?"
                })
            )

            return Response("OK")
        except Exception as e:
            # This allows you to see the error in 'Events' if it fails again
            return Response(f"Internal Error: {str(e)}", status=200)

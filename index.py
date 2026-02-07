from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # 1. BOT TRAFFIC
        if request.method == "POST":
            try:
                data = await request.json()
                if "message" not in data:
                    return Response("OK")
                
                chat_id = data["message"]["chat"]["id"]
                
                # Direct access to environment variables
                token = self.env.TELEGRAM_TOKEN
                
                # Send the message
                resp = await fetch(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    method="POST",
                    body=json.dumps({
                        "chat_id": chat_id,
                        "text": "Hello! The Lead Fountain Concierge is now fully connected and ready to assist."
                    }),
                    headers={"Content-Type": "application/json"}
                )
                
                return Response("OK")
            except Exception as e:
                # This helps us see errors in the 'Events' logs if Telegram rejects us
                return Response(f"Error: {str(e)}")

        # 2. WEBSITE TRAFFIC
        html = "<h1>Lead Fountain</h1><p>Senior Client Concierge is Online.</p>"
        return Response(html, headers={"Content-Type": "text/html"})

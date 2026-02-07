from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # 1. HANDLE TELEGRAM BOT (POST)
        if request.method == "POST":
            try:
                data = await request.json()
                chat_id = data["message"]["chat"]["id"]
                
                # Test response to prove the bot is alive
                reply = "Lead Fountain Concierge is Active and Online!"
                
                tg_url = f"https://api.telegram.org/bot{self.env.TELEGRAM_TOKEN}/sendMessage"
                await fetch(tg_url, {
                    "method": "POST",
                    "body": json.dumps({"chat_id": chat_id, "text": reply}),
                    "headers": {"Content-Type": "application/json"}
                })
                return Response("OK")
            except Exception as e:
                return Response(f"Error: {str(e)}")

        # 2. HANDLE WEBSITE (GET)
        # This keeps your website alive inside the bot
        html_site = """
        <!DOCTYPE html>
        <html>
        <head><title>Lead Fountain</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1>Lead Fountain</h1>
            <p>Our Senior Client Concierge is now active on Telegram.</p>
        </body>
        </html>
        """
        return Response(html_site, headers={"Content-Type": "text/html"})

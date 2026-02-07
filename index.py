import json
from js import Response, fetch

class Default:
    def __init__(self, env):
        self.env = env

    async def fetch(self, request):
        # 1. THE BOT LOGIC (POST requests)
        if request.method == "POST":
            try:
                data = await request.json()
                chat_id = data["message"]["chat"]["id"]
                # Just a simple test reply to prove it works
                reply = "Lead Fountain Concierge Active!"
                
                tg_url = f"https://api.telegram.org/bot{self.env.TELEGRAM_TOKEN}/sendMessage"
                await fetch(tg_url, {
                    "method": "POST",
                    "body": json.dumps({"chat_id": chat_id, "text": reply}),
                    "headers": {"Content-Type": "application/json"}
                })
                return Response.new("OK")
            except:
                return Response.new("OK")

        # 2. THE WEBSITE LOGIC (GET requests)
        # Paste your actual HTML code between the triple quotes below
        html_site = """
        <!DOCTYPE html>
        <html>
        <head><title>Lead Fountain</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h1>Lead Fountain</h1>
            <p>Our Senior Client Concierge is now on Telegram.</p>
        </body>
        </html>
        """
        return Response.new(html_site, headers={"Content-Type": "text/html"})

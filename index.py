from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # 1. BOT TRAFFIC (POST)
        if request.method == "POST":
            try:
                data = await request.json()
                chat_id = data["message"]["chat"]["id"]
                user_text = data["message"].get("text", "")

                # Send a simple confirmation back to Telegram
                tg_url = f"https://api.telegram.org/bot{self.env.TELEGRAM_TOKEN}/sendMessage"
                await fetch(tg_url, {
                    "method": "POST",
                    "body": json.dumps({"chat_id": chat_id, "text": "Lead Fountain Concierge is Online!"}),
                    "headers": {"Content-Type": "application/json"}
                })
                return Response.new("OK")
            except:
                return Response.new("OK")

        # 2. WEBSITE TRAFFIC (GET)
        # This replaces the blank screen with your actual site
        html_site = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Lead Fountain | Senior Client Concierge</title>
            <style>
                body { font-family: 'Helvetica', sans-serif; background: #f4f7f6; color: #333; text-align: center; padding: 100px 20px; }
                .container { max-width: 600px; margin: auto; background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
                h1 { color: #1a5f7a; }
                p { font-size: 1.2rem; line-height: 1.6; }
                .btn { display: inline-block; margin-top: 20px; padding: 12px 25px; background: #1a5f7a; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Lead Fountain</h1>
                <p>Our Senior Client Concierge is now assisting clients exclusively via Telegram for enhanced security and speed.</p>
                <a href="https://t.me/YOUR_BOT_USERNAME" class="btn">Chat with Concierge</a>
            </div>
        </body>
        </html>
        """
        return Response.new(html_site, headers={"Content-Type": "text/html;charset=UTF-8"})

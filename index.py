from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # 1. BOT TRAFFIC (POST)
        if request.method == "POST":
            try:
                body = await request.json()
                chat_id = body["message"]["chat"]["id"]

                # FIX 1: Access token safely using getattr to prevent crash
                token = getattr(self.env, "TELEGRAM_TOKEN", None)
                
                if not token:
                    # If token is missing, we stop here but don't crash the worker
                    return Response("Missing TELEGRAM_TOKEN variable in Cloudflare Settings")

                tg_url = f"https://api.telegram.org/bot{token}/sendMessage"
                
                await fetch(tg_url, {
                    "method": "POST",
                    "body": json.dumps({
                        "chat_id": chat_id, 
                        "text": "Lead Fountain Concierge is Online and Fixed!"
                    }),
                    "headers": {"Content-Type": "application/json"}
                })
                
                # FIX 2: Use Response() instead of Response.new()
                return Response("OK")
            except Exception as e:
                return Response(f"Internal Error: {str(e)}")

        # 2. WEBSITE TRAFFIC (GET)
        html_site = "<h1>Lead Fountain Concierge</h1><p>Active on Telegram.</p>"
        return Response(html_site, headers={"Content-Type": "text/html;charset=UTF-8"})

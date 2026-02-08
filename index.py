from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # 1. BROWSER STATUS
        if request.method == "GET":
            return Response("<h1>Lead Fountain</h1><p>Emergency Bypass Mode: Active.</p>", 
                            headers={"Content-Type": "text/html"})

        # 2. BOT HANDLING
        try:
            body = await request.json()
            if "message" not in body:
                return Response("OK")

            chat_id = body["message"]["chat"]["id"]
            
            # HARDCODED TOKEN - Bypassing the broken Cloudflare Variables
            token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"
            
            # SEND REPLY
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            await fetch(url, 
                method="POST", 
                headers={"Content-Type": "application/json"},
                body=json.dumps({
                    "chat_id": chat_id, 
                    "text": "The Bypass is working! I can finally hear you."
                })
            )

            return Response("OK")

        except Exception as e:
            return Response("OK")

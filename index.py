from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "GET":
            return Response("Worker is active. Telegram connection confirmed.")

        try:
            # 1. Parse incoming data
            body = await request.json()
            
            if "message" in body:
                chat_id = body["message"]["chat"]["id"]
                user_text = body["message"].get("text", "")
                
                # 2. HARDCODED TOKEN (The one we know works)
                token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"
                
                # 3. FORCE THE MESSAGE OUT
                # Instead of returning JSON, we manually call Telegram's API
                await fetch(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    method="POST",
                    headers={"Content-Type": "application/json"},
                    body=json.dumps({
                        "chat_id": chat_id,
                        "text": f"Got it! You said: {user_text}"
                    })
                )

            return Response("OK", status=200)
            
        except Exception as e:
            # This logs the error so we can see it in your next log paste
            print(f"Error: {str(e)}")
            return Response("OK", status=200)

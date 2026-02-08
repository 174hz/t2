from workers import Response, WorkerEntrypoint
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # 1. GET - Browser check
        if request.method == "GET":
            return Response("Bot is active. Waiting for POST.")

        # 2. POST - Telegram check
        try:
            # We use await request.json() directly
            data = await request.json()
            
            if "message" in data:
                cid = data["message"]["chat"]["id"]
                text = data["message"].get("text", "")

                # Direct Webhook Response - No token or fetch needed
                return Response(
                    json.dumps({
                        "method": "sendMessage",
                        "chat_id": cid,
                        "text": f"Connected! You said: {text}"
                    }),
                    headers={"Content-Type": "application/json"}
                )
        except:
            pass
            
        return Response("OK")

from workers import Response, WorkerEntrypoint
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # 1. SIMPLEST GET
        if request.method == "GET":
            return Response("Bot Status: Ready. Waiting for messages.", headers={"Content-Type": "text/plain"})

        # 2. SIMPLEST POST (CALLBACK METHOD)
        try:
            # Using request.json() directly is safer in this version
            data = await request.json()
            
            if "message" in data:
                chat_id = data["message"]["chat"]["id"]
                user_text = data.get("message", {}).get("text", "Hello")

                # The reply is sent as the direct HTTP response to Telegram
                # This requires NO tokens and NO environment variables
                reply = {
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": f"Lead Fountain reached! You said: {user_text}"
                }
                
                return Response(
                    json.dumps(reply),
                    headers={"Content-Type": "application/json"}
                )

            return Response("OK")
        except Exception:
            # If parsing fails, we must still return a 200 to satisfy Telegram
            return Response("OK")

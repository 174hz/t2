from workers import Response, WorkerEntrypoint
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # 1. BROWSER STATUS CHECK
        if request.method == "GET":
            return Response("Status: Online and listening for Telegram.")

        # 2. TELEGRAM MESSAGE HANDLER
        try:
            # Parse the incoming message
            data = await request.json()
            
            if "message" in data:
                chat_id = data["message"]["chat"]["id"]
                user_text = data["message"].get("text", "")

                # THE DIRECT CALLBACK:
                # We return the reply directly to Telegram as the HTTP Response.
                # No token or fetch() required!
                return Response(
                    json.dumps({
                        "method": "sendMessage",
                        "chat_id": chat_id,
                        "text": f"Success! I received: {user_text}"
                    }),
                    headers={"Content-Type": "application/json"}
                )

            return Response("OK")
        except Exception:
            # If parsing fails, we return a 200 so Telegram stops retrying
            return Response("OK")

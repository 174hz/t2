from workers import Response, WorkerEntrypoint
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # 1. BROWSER CHECK
        if request.method == "GET":
            return Response("Bot Status: ONLINE. Send a message to the bot.")

        # 2. TELEGRAM MESSAGE HANDLER
        try:
            # Parse the incoming JSON from Telegram
            body = await request.json()
            
            # Extract Chat ID
            if "message" in body:
                chat_id = body["message"]["chat"]["id"]
                
                # We return the instructions DIRECTLY to Telegram as the HTTP Response
                # This is the most reliable way to avoid connection/token errors.
                reply = {
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": "The bot is now responding via direct callback!"
                }
                
                return Response(
                    json.dumps(reply),
                    headers={"Content-Type": "application/json"}
                )
        except Exception as e:
            # If there's an error, returning

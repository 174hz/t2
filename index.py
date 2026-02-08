from workers import Response, WorkerEntrypoint
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # GET - Check this in your browser
        if request.method == "GET":
            return Response("FORCE RESET: If you see this, the code is live.", headers={"Content-Type": "text/plain"})

        # POST - Handle Telegram
        try:
            # We use a safer way to get the JSON to avoid 500 errors
            raw_text = await request.text()
            data = json.loads(raw_text)
            
            if "message" in data:
                chat_id = data["message"]["chat"]["id"]
                
                # We HARDCODE the reply to bypass the variable binding issue
                # We return it as a direct response to Telegram
                return Response(
                    json.dumps({
                        "method": "sendMessage",
                        "chat_id": chat_id,
                        "text": "The Lead Fountain Bot has been FORCE RESET and is now communicating."
                    }),
                    headers={"Content-Type": "application/json"}
                )
            
            return Response("OK")
        except Exception as e:
            # If it fails, return the error so we can see it in 'getWebhookInfo'
            return Response(f"Fail: {str(e)}", status=200)

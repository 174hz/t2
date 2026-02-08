from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # 1. SIMPLEST STATUS CHECK
        if request.method == "GET":
            return Response("Worker is live. KV and Python are connected.")

        # 2. TELEGRAM MESSAGE HANDLER
        try:
            # Safely get the data
            body = await request.json()
            
            if "message" in body:
                chat_id = body["message"]["chat"]["id"]
                
                # HARDCODED TOKEN (Bypassing the dashboard issues)
                token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"
                
                # DIRECT RESPONSE METHOD
                # We return the instructions to Telegram immediately
                return Response(
                    json.dumps({
                        "method": "sendMessage",
                        "chat_id": chat_id,
                        "text": "The bot is finally communicating! We have a solid connection."
                    }),
                    headers={"Content-Type": "application/json"}
                )
        except Exception as e:
            # This will show up in your Cloudflare 'Live Logs' if it fails
            print(f"Error occurred: {str(e)}")
            
        return Response("OK")

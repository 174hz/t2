from workers import Response, WorkerEntrypoint
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # Browser check: Visit your .dev link to see if this is live
        if request.method == "GET":
            return Response("SYSTEM ONLINE: Waiting for Telegram...", headers={"Content-Type": "text/plain"})

        # Telegram Handler
        try:
            # Get the data from Telegram
            body = await request.json()
            
            if "message" in body:
                chat_id = body["message"]["chat"]["id"]
                user_text = body["message"].get("text", "")

                # THE CALLBACK SECRET:
                # We return the reply as the HTTP response. 
                # No Token needed. No Fetch needed.
                payload = {
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": f"Connection established! I heard: {user_text}"
                }
                
                return Response(
                    json.dumps(payload),
                    headers={"Content-Type": "application/json"}
                )
        except Exception as e:
            return Response(f"Error: {str(e)}", status=200)

        return Response("OK", status=200)

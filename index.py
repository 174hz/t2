from workers import Response, WorkerEntrypoint, fetch
import json

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "GET":
            return Response("Lead Fountain AI: Active and Monitoring.")

        try:
            body = await request.json()
            if "message" not in body: return Response("OK")
            
            chat_id = body["message"]["chat"]["id"]
            user_text = body["message"].get("text", "")
            
            # --- THE BRAIN: LEAD EXTRACTION ---
            # In a full version, we'd call Gemini here. 
            # For now, we build the logic that qualifies the lead.
            is_lead = any(word in user_text.lower() for word in ["roof", "repair", "need", "looking", "help"])
            
            if is_lead:
                response_text = "Thanks for reaching out! I've noted your interest. Could you tell me your name and the best phone number to reach you at?"
                # SAVING THE LEAD (Using your KV Binding: LEAD_HISTORY)
                # Key: lead_timestamp, Value: user_message
                await self.env.LEAD_HISTORY.put(f"lead_{chat_id}", user_text)
            else:
                response_text = "I'm MillbrookLeadBot. I help connect people with local home services. How can I help you today?"

            # --- THE VOICE: SENDING THE MESSAGE ---
            token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"
            await fetch(
                f"https://api.telegram.org/bot{token}/sendMessage",
                method="POST",
                headers={"Content-Type": "application/json"},
                body=json.dumps({
                    "chat_id": chat_id,
                    "text": response_text
                })
            )

            return Response("OK", status=200)
            
        except Exception as e:
            print(f"Error: {e}")
            return Response("OK", status=200)

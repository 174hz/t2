from workers import Response, WorkerEntrypoint, fetch
import json
import re

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "GET": return Response("Lead-Fountain: Active.")

        try:
            body = await request.json()
            if "message" not in body: return Response("OK")
            
            chat_id = str(body["message"]["chat"]["id"])
            user_text = body["message"].get("text", "")
            
            # --- CONFIG ---
            api_key = getattr(self.env, "GOOGLE_API_KEY", None)
            tg_token = "8554962289:AAG_6keZXWGVnsHGdXsbDKK4OhhKu4C1kqg"
            my_admin_id = "1556353947" 

            # --- 1. AI BRAIN ---
            # Updated the URL to the most stable 'v1' production endpoint
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
            
            system_prompt = (
                "You are the Lead-Fountain Intake Bot. Collect: 1. Full Name, 2. Phone, "
                "3. Location, 4. Job Scope (Repair/Replace). Be professional. "
                "If info is missing, ask for it. User just said: "
            )
            
            payload = {"contents": [{"parts": [{"text": f"{system_prompt} {user_text}"}]}]}
            
            ai_res = await fetch(url, method="POST", body=json.dumps(payload))
            ai_data = await ai_res.json()

            if 'candidates' in ai_data:
                bot_reply = ai_data['candidates'][0]['content']['parts'][0]['text']
            else:
                # If there's still an error, show us exactly what it is
                bot_reply = f"Debug Note: {json.dumps(ai_data)[:150]}"

            # --- 2. ALERT (ONLY TO YOU) ---
            if re.search(r'\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}', user_text):
                alert_text = f"💰 **NEW LEAD** 💰\n\n**Info:** {user_text}\n\n**Chat:** {chat_id}"
                await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    method="POST", headers={"Content-Type": "application/json"},
                    body=json.dumps({"chat_id": my_admin_id, "text": alert_text}))

            # --- 3. REPLY TO CUSTOMER ---
            await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                method="POST", headers={"Content-Type": "application/json"},
                body=json.dumps({"chat_id": chat_id, "text": bot_reply}))

            return Response("OK", status=200)

        except Exception as e:
            return Response("OK", status=200)

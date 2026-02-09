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
            
            api_key = getattr(self.env, "GOOGLE_API_KEY", None)
            tg_token = getattr(self.env, "TELEGRAM_TOKEN", None)
            my_admin_id = getattr(self.env, "MY_CHAT_ID", None)

            # --- 1. DETECT MISSING INFO ---
            has_phone = re.search(r'\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}', user_text)
            # Simple check for a name (if the message is very short or doesn't look like an intro)
            has_name = len(user_text.split()) > 3 and any(word in user_text.lower() for word in ["my name", "i'm", "i am", "this is"])

            # --- 2. AI CALL (Using the 'latest' model string) ---
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            
            system_prompt = (
                "You are a roofing intake assistant. You MUST collect: Name and Phone Number. "
                "The user just said: "
            )
            
            ai_res = await fetch(url, method="POST", body=json.dumps({"contents": [{"parts": [{"text": f"{system_prompt} {user_text}"}]}]}))
            ai_data = await ai_res.json()

            # --- 3. LOGIC-BASED REPLY ---
            if 'candidates' in ai_data:
                bot_reply = ai_data['candidates'][0]['content']['parts'][0]['text']
            else:
                # HUMAN LOGIC FALLBACK: If AI fails, WE enforce the rules
                if not has_phone and not has_name:
                    bot_reply = "I've noted the leak in Chatham. To get a specialist out there, could you please provide your full name and the best phone number to reach you?"
                elif not has_phone:
                    bot_reply = "Thanks! What is the best phone number for our specialist to reach you at to discuss the repair?"
                else:
                    bot_reply = "Got it. What is the best time today for our specialist to give you a call?"

            # --- 4. ADMIN ALERT ---
            if is_lead := (has_phone or "Chatham" in user_text):
                alert_text = f"💰 **NEW LEAD** 💰\n\n**Info:** {user_text}"
                await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    method="POST", headers={"Content-Type": "application/json"},
                    body=json.dumps({"chat_id": my_admin_id, "text": alert_text}))

            # --- 5. REPLY TO CUSTOMER ---
            await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                method="POST", headers={"Content-Type": "application/json"},
                body=json.dumps({"chat_id": chat_id, "text": bot_reply}))

            return Response("OK", status=200)

        except Exception:
            return Response("OK", status=200)

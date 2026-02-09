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
            tg_token = getattr(self.env, "TELEGRAM_TOKEN", None)
            my_admin_id = str(getattr(self.env, "MY_CHAT_ID", None))

            # --- 1. BRANDED AI PROMPT ---
            # We explicitly tell the AI to use your premium branding phrases
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            brand_prompt = (
                "You are the Lead-Fountain Assistant. You must be professional and premium. "
                "Your goal is to get the user's Name, Phone Number, and Best Time to call. "
                "Always mention that we will have one of our 'vetted and verified specialists' contact them. "
                "User says: "
            )

            # --- 2. THE AI CALL ---
            bot_reply = ""
            try:
                ai_res = await fetch(url, method="POST", body=json.dumps({"contents": [{"parts": [{"text": f"{brand_prompt} {user_text}"}]}]}))
                ai_data = await ai_res.json()
                bot_reply = ai_data['candidates'][0]['content']['parts'][0]['text']
            except:
                # PREMIUM FALLBACK: Used if AI fails to connect
                bot_reply = (
                    "Thanks for reaching out to us. May I have your name, the phone number where you can be reached, "
                    "and the time that's most convenient? I will then have one of our vetted and verified specialists contact you."
                )

            # --- 3. PRIVATE ADMIN ALERT (Only to You) ---
            # We check if it's a lead and ensure the message goes to the admin, NOT the user.
            is_lead_info = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', user_text) or "leak" in user_text.lower()
            
            if is_lead_info and my_admin_id:
                alert_text = f"💰 **LEAD CAPTURED** 💰\n\n**Details:** {user_text}\n**Chat ID:** {chat_id}"
                # Send to ADMIN
                await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    method="POST", headers={"Content-Type": "application/json"},
                    body=json.dumps({"chat_id": my_admin_id, "text": alert_text}))

            # --- 4. PUBLIC CUSTOMER REPLY (Only to Customer) ---
            # If the admin is testing, they will see this too.
            await fetch(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                method="POST", headers={"Content-Type": "application/json"},
                body=json.dumps({"chat_id": chat_id, "text": bot_reply}))

            return Response("OK", status=200)

        except Exception:
            return Response("OK", status=200)

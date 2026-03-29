import os
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)

# Load secrets
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET") 
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")

# Use ONE Master Database ID here. 
# Use Linked Views with Date Filters on your Monthly pages in Notion.
DATABASE_ID = os.environ.get("DATABASE_ID")

groq_client = Groq(api_key=GROQ_API_KEY)

@app.route('/api/webhook', methods=['POST'])
def handle_sms():
    # 1. Security Check
    provided_secret = request.headers.get("Authorization")
    if provided_secret != f"Bearer {WEBHOOK_SECRET}":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    sms_text = data.get("text", "")
    
    if not sms_text:
        return jsonify({"error": "No text provided"}), 400

    try:
        # 2. Ask Groq API to parse the UPI SMS
        system_prompt = """
        You are a financial parser for Indian UPI/Bank SMS messages. 
        Extract the following data:
        - amount (number)
        - purpose (string: who the money was sent to, or what was bought)
        - bank_account (string: exact bank name and account/phone number if present, e.g., 'Union Bank Ph: 9553677784')
        - type (string: strictly 'Debited Amount' if money left the account, or 'Credited Amount' if money was received)
        
        Respond ONLY in valid JSON format: 
        {"amount": 150, "purpose": "sand paper", "bank_account": "Union Bank Ph: 9553677784", "type": "Debited Amount"}
        """

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": sms_text}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0,
            response_format={"type": "json_object"} 
        )
        
        parsed_data = json.loads(chat_completion.choices[0].message.content)

        # 3. Handle Dates
        # Grabs the current time the webhook is received
        now = datetime.now()
        iso_date = now.isoformat() # For the Notion Date property
        display_date = now.strftime("%B %d, %Y") # For the string Title property (e.g., "March 29, 2026")

        # 4. Send parsed data to Notion
        notion_url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # Matches your exact Notion table structure
        notion_data = {
            "parent": {"database_id": DATABASE_ID},
            "properties": {
                # 'Aa Date' (String/Title Property)
                "Date": {"title": [{"text": {"content": display_date}}]},
                
                # 'Date (1)' (Actual Date Property)
                "Date (1)": {"date": {"start": iso_date}},
                
                # 'Bank A/c Ph: No' (Select Property)
                "Bank A/c Ph: No": {"select": {"name": parsed_data.get("bank_account", "Unknown Bank")}},
                
                # 'Type' (Select Property)
                "Type": {"select": {"name": parsed_data.get("type", "Debited Amount")}},
                
                # 'Amount' (Number Property)
                "Amount": {"number": parsed_data.get("amount", 0)},
                
                # 'Purpose' (Rich Text Property)
                "Purpose": {"rich_text": [{"text": {"content": parsed_data.get("purpose", "Unknown")}]}
            }
        }
        
        notion_res = requests.post(notion_url, headers=headers, json=notion_data)
        notion_res.raise_for_status() 

        return jsonify({"status": "success", "parsed": parsed_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
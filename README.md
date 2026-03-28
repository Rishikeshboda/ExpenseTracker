# 💸 UPI SMS to Notion Tracker

Hey! This is a little weekend side project I built to solve a personal annoyance: manually entering every single UPI transaction into my Notion expense tracker. 

Whenever I buy a chai, pay a friend, or receive money, my bank sends an SMS. This project intercepts that SMS, uses a lightning-fast LLM to figure out what it means, and automatically logs it into my Notion database. 

No manual data entry. Total magic. ✨

## 🧠 How it Works

1. **The Trigger:** My phone (using Tasker/MacroDroid/Shortcuts) listens for bank SMS messages.
2. **The Webhook:** When an SMS arrives, the phone silently fires a POST request to a Vercel serverless function.
3. **The Brains:** The Flask function sends the text to the **Groq API** (running Llama 3.3 70B Versatile). I specifically prompted it to understand Indian UPI messages and extract the `Amount`, `Party`, `Category`, and whether it's an `Income` or `Expense`.
4. **The Destination:** The parsed JSON is immediately pushed to my **Notion API**, creating a neat little row in my database.

## 🛠️ Tech Stack
* **Python / Flask** (for the webhook receiver)
* **Ngrok** (for local tunnel to public URL)
* **Groq API** (Because Llama 3 running on LPUs is ridiculously fast and free)
* **Notion API** (The database)

## 🚀 Setting it up yourself

If you want to fork this and use it, go for it! You'll need to set up a few things:

1. **Notion:** Create a database with these exact columns (case-sensitive):
   * `Party` (Title property)
   * `Amount` (Number property)
   * `Type` (Select property: "Expense" or "Income")
   * `Category` (Select property: e.g., "Food", "Transport")
2. **Keys & Secrets:** You'll need to grab a few API keys and set them in your `.env` file (copy from `.env.example`):
   * `GROQ_API_KEY`: Get this from the Groq console.
   * `NOTION_API_KEY`: Get this from Notion's developer dashboard.
   * `DATABASE_ID`: The 32-character string in your Notion database URL.
   * `WEBHOOK_SECRET`: Make up a password! You'll put this in your phone's automation app so random internet bots can't spam your Notion.

## ⚠️ Disclaimer
This is just a personal side project I built to scratch my own itch. It works great for my specific bank's SMS format, but you might need to tweak the Groq system prompt in `webhook.py` if your bank sends slightly different messages. 

Since it processes financial SMS data, please keep your `.env` keys completely private and use the `WEBHOOK_SECRET` to secure your endpoint!

## 🔧 Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask app
python -c "from api.index import app; app.run(port=5000)"

# In another terminal, start ngrok
ngrok http 5000
```
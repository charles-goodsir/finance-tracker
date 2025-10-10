# 🤖 AI Classification Setup Guide

Your finance tracker now includes **AI-powered transaction classification** using Google Gemini!

## 🎯 What This Does

- **Hybrid Classification**: Uses rule-based matching first (fast & free), then AI for uncertain cases
- **Smart Fallback**: AI only activates when rules don't match
- **Zero Cost**: Google Gemini offers a generous free tier
- **Easy Toggle**: Can be enabled/disabled via environment variable

---

## 🔑 Step 1: Get Your FREE Gemini API Key

1. Visit: **https://makersuite.google.com/app/apikey**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key (starts with `AIza...`)

**No credit card required!** ✅

---

## 💻 Step 2: Local Development Setup

### Add to your environment:

```bash
# In your terminal
export GEMINI_API_KEY="your_api_key_here"
```

Or create a `.env` file in the `backend/` directory:

```bash
# backend/.env
GEMINI_API_KEY=your_api_key_here
```

### Install dependencies:

```bash
cd backend
pip install google-generativeai
```

### Test it works:

```bash
cd backend
python test_ai_classifier.py
```

You should see AI classification in action! 🎉

---

## ☁️ Step 3: AWS Deployment

### Deploy with AI enabled:

```bash
cd sam-backend

# Build
sam build

# Deploy with Gemini API key
sam deploy --parameter-overrides \
  TelegramBotToken=your_telegram_token \
  TelegramChatId=your_chat_id \
  GeminiApiKey=your_gemini_key
```

### Check AI status:

```bash
curl https://your-api-url/ai/status
```

Should return:
```json
{
  "enabled": true,
  "provider": "Google Gemini",
  "model": "gemini-pro",
  "library_available": true,
  "api_key_configured": true
}
```

---

## 🧪 Step 4: Test AI Classification

### Test via API endpoint:

```bash
curl -X POST "https://your-api-url/ai/classify?description=MYSTERY%20CAFE&amount=-25.50"
```

### Test in desktop app:

1. Open the app
2. Import a CSV with unusual merchants
3. Watch the console for `🤖 Using AI for:` messages
4. Check if categories are more accurate!

---

## 📊 How It Works

```
Transaction → Rule-Based Classifier
                     ↓
              Match found? → YES → Return category ✅
                     ↓
                    NO
                     ↓
            AI Classifier (Gemini)
                     ↓
              Return AI category 🤖
```

**Example:**
- `"WOOLWORTHS"` → **Rule match** → "Groceries" (instant)
- `"MYSTERY CAFE"` → **No rule** → AI analyzes → "Dining Out" 🤖

---

## 🎛️ Configuration Options

### Disable AI (use rules only):

In `backend/.env`:
```bash
# Don't set GEMINI_API_KEY or set it to empty
GEMINI_API_KEY=
```

### Force AI for all transactions:

Modify `classifier.py`:
```python
# Use AI even when rules match
def classify(description, amount, use_ai: bool = True):
    # ... always call AI
    return classify_with_ai(description, amount)
```

---

## 💰 Cost Breakdown

### Free Tier (Gemini):
- **60 requests/minute** - plenty for personal use
- **1500 requests/day** - more than enough
- **No credit card required**

### Paid Alternatives (if you want):
- OpenAI GPT-3.5: ~$0.0005/transaction
- OpenAI GPT-4: ~$0.01/transaction
- Anthropic Claude: ~$0.01/transaction

**Recommendation**: Stick with free Gemini! 🎉

---

## 🔍 Monitoring AI Usage

### Check logs:

```bash
# See when AI is used
cd backend
python -c "
from classifier import classify
print(classify('MYSTERY MERCHANT', -50.00, use_ai=True))
"
```

Look for: `🤖 Using AI for: MYSTERY MERCHANT`

### View classification history:

Check your Lambda logs:
```bash
cd sam-backend
sam logs -n FinanceTrackerFunction --tail
```

---

## 🐛 Troubleshooting

### "AI classification disabled"
- Check your API key is set correctly
- Verify the key starts with `AIza`
- Try regenerating the key

### "google-generativeai not installed"
```bash
cd backend
pip install google-generativeai
```

### AI returns wrong categories
- The prompt can be tuned in `ai_classifier.py`
- Add more specific rules to the prompt
- Or add merchant to rule-based classifier

### "API key not configured"
```bash
# Check environment
echo $GEMINI_API_KEY

# Set it
export GEMINI_API_KEY="your_key_here"
```

---

## 🚀 Next Steps

Now that you have AI working:

1. **Add Chat Interface**: Ask questions about your finances in natural language
2. **Predictive Analytics**: Use AI to forecast future spending
3. **Receipt OCR**: Upload receipt photos, extract data with AI
4. **Smart Insights**: AI-generated financial advice
5. **Learning Mode**: Let AI learn from your corrections

---

## 📚 API Reference

### GET `/ai/status`
Check if AI classification is available.

**Response:**
```json
{
  "enabled": true,
  "provider": "Google Gemini",
  "model": "gemini-pro",
  "library_available": true,
  "api_key_configured": true
}
```

### POST `/ai/classify`
Manually classify a transaction using AI.

**Parameters:**
- `description` (string): Transaction description
- `amount` (float): Transaction amount

**Response:**
```json
{
  "description": "MYSTERY CAFE",
  "amount": -25.50,
  "category": "Dining Out",
  "method": "ai"
}
```

---

## 🎉 Success!

You now have **AI-powered financial intelligence** in your tracker!

Questions? Check the code in:
- `backend/ai_classifier.py` - AI logic
- `backend/classifier.py` - Hybrid classification
- `backend/app.py` - API endpoints


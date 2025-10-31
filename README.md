# 💰 Finance Tracker 2.0

A comprehensive personal finance management system with **AI-powered classification**, AWS cloud deployment, and a modern PyQt6 desktop interface.

## 🚦 First‑Time Users: 10‑Minute Setup

Follow this section end‑to‑end if you’re new. It covers desktop setup, API config, and your first sync.

### 1) Install and run the desktop app

```bash
cd desktop-app
pip install -r requirements.txt
python main_gui.py
```

### 2) Configure your API URL and secrets

Create a `.env` file in the project root:

```env
# AWS API Gateway base URL (no trailing slash)
AWS_API_URL="https://<api-id>.execute-api.<region>.amazonaws.com/Prod"

# Optional integrations
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
GEMINI_API_KEY=your_gemini_api_key
```

Restart the desktop app so it picks up the `.env`.

### 3) First‑run workflow (repeat monthly)

1. Go to the 🏦 Accounts tab → enter balances for Savings, Bills, Main, and Credit Card → Save
2. Click 📸 Save Monthly Snapshot for today’s date
3. Go to 📁 CSV Import → choose account → select bank CSV → review categories → Commit to AWS
4. Open 📊 Dashboard → click Refresh to load stats and insights

Tip: On the 10th each month, an EventBridge cron can send a Telegram reminder.

### 4) How the numbers are calculated

- Spending excludes: `Transfers`, `Payment`, `Cash Withdrawal`, `Credit Card Payments`
- Savings rate = 100 × (income − spending) / income
- Credit utilization = abs(credit debt) / credit limit (limit is 4000 by default in UI)

### 5) Troubleshooting quick fixes

- Insights blank? Ensure `.env` has `AWS_API_URL`, then click Refresh
- Insights show only emojis? Ensure the insights label text color is dark (e.g., `#1a202c`)
- AI rate‑limited? Rule‑based classification and learning reduce calls; corrections improve future imports

## ✨ Key Features

### 🤖 **NEW: AI-Powered Classification**
- **Hybrid Intelligence**: Rule-based matching + Google Gemini AI fallback
- **Smart Categorization**: Automatically classifies transactions you've never seen before
- **Zero Cost**: Uses Google Gemini's free tier (no credit card required!)
- **Privacy-First**: Only sends transaction description & amount to AI

### 💳 **Transaction Management**
- Add, view, and track income/expenses across multiple accounts
- Smart CSV import with automatic bank statement parsing
- Transfer detection between accounts (excluded from insights)
- Multi-account support (Savings, Bills, Main, Credit Card)

### 📊 **Financial Intelligence**
- **Net Worth Tracking**: Assets minus liabilities (credit card debt)
- **Smart Insights**: AI-generated spending alerts and savings suggestions
- **Financial Health Score**: Real-time assessment of your financial wellness
- **Goal Setting & Tracking**: Set savings goals and monitor progress

### 🎯 **Goal Management**
- Create custom financial goals with target amounts
- Track progress automatically as you save
- Visual progress indicators
- Milestone notifications via Telegram

### 📱 **Telegram Integration**
- Real-time transaction notifications
- Daily/weekly financial summaries
- Goal achievement alerts
- Budget warnings

### 🖥️ **Modern Desktop App (PyQt6)**
- Beautiful dark mode interface
- Real-time dashboard with stats
- Transaction filtering and search
- CSV import with account selection
- Offline support with sync

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- AWS CLI configured
- SAM CLI installed
- (Optional) Telegram Bot Token for notifications
- (Optional) Google Gemini API Key for AI classification

### Desktop App

1. **Setup and run**:
   ```bash
   cd desktop-app
   pip install -r requirements.txt
   python main_gui.py
   ```

2. **Configure API**:
   - Create `.env` in the project root with `AWS_API_URL`
   - Restart the app so the environment is picked up
   - (Optional) Add Telegram and Gemini keys

### Backend API (Local)

1. **Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Create `.env` file**:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   GEMINI_API_KEY=your_gemini_key  # Optional for AI
   ```

3. **Run locally**:
   ```bash
   uvicorn app:app --reload
   ```

4. **Access**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

## 🧭 Using Finance Tracker Without AWS

You can run the app fully offline or without deploying any AWS resources.

### Option 1 — Desktop‑only (no backend)

- Leave `AWS_API_URL` unset in your project‑root `.env` (or omit `.env`).
- Works offline using the local SQLite cache.
- You can: import CSVs, edit categories, and view a basic dashboard from local data.
- Not available: Cloud sync, Insights/Health, Telegram notifications, learning system.

Steps:
```bash
cd desktop-app
pip install -r requirements.txt
python main_gui.py
```

### Option 2 — Local API (no cloud)

Run the backend locally and point the desktop app to it.

1) Start the API locally:
```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
```

2) Point the desktop app to your local API in project‑root `.env`:
```env
AWS_API_URL="http://localhost:8000"
```

3) (Optional) Avoid any AWS dependency by running DynamoDB Local:
```bash
docker run -p 8001:8000 amazon/dynamodb-local
# If your config supports it, set an endpoint override for the backend:
# DYNAMODB_ENDPOINT_URL=http://localhost:8001
```

With a working local store (AWS or DynamoDB Local), Insights, Financial Health, and the learning system will function as normal.

## ☁️ AWS Deployment

### Deploy to AWS

```bash
cd sam-backend
sam build
sam deploy --parameter-overrides \
  TelegramBotToken=your_telegram_token \
  TelegramChatId=your_chat_id \
  GeminiApiKey=your_gemini_key
```

### AWS Resources Created
- **Lambda Function**: FastAPI application
- **DynamoDB Tables**: 
  - Transactions
  - Categories
  - Recurring Transactions
  - Goals
  - Insights
  - Account Balances
- **API Gateway**: RESTful API endpoints
- **EventBridge/CloudWatch**: Monthly Telegram reminder schedule

## 🤖 AI Setup (Optional)

### Get FREE Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key" (no credit card!)
4. Copy the key

### Configure AI

**Local Development**:
```bash
export GEMINI_API_KEY="your_key_here"
```

**AWS Deployment**:
Already configured! Just pass the key during `sam deploy`.

### Test AI Classification

```bash
cd backend
python test_ai_classifier.py
```

You'll see:
- 📋 Rule-based matches (instant, free)
- 🤖 AI classifications (for unknown merchants)

See [AI_SETUP.md](AI_SETUP.md) for detailed documentation.

## 📊 API Endpoints

### Core Transactions
- `POST /transactions` - Add new transaction
- `GET /transactions` - List transactions (with filters)
- `POST /transaction/commit-bulk` - Bulk commit from CSV

### Smart Classification
- `POST /import-bank-csv` - Import & auto-classify bank CSV
- `GET /ai/status` - Check AI availability
- `POST /ai/classify` - Manually classify with AI

### Financial Intelligence
- `GET /insights` - Get spending alerts & suggestions (top‑level keys)
- `GET /accounts/networth` - Calculate net worth
- `GET /accounts/balances` - Get all account balances
- `POST /accounts/balance` - Update account balance

### Goals
- `POST /goals` - Create financial goal
- `GET /goals` - List all goals
- `PUT /goals/{goal_id}` - Update goal progress

### Categories & Recurring
- `GET /categories` - List all categories
- `POST /recurring-transactions` - Add recurring transaction
- `GET /recurring-transactions` - List recurring transactions

## 🗂️ Project Structure

```
finance-tracker/
├── backend/                    # FastAPI application
│   ├── app.py                 # Main API endpoints
│   ├── aws_db.py              # DynamoDB integration
│   ├── classifier.py          # Rule-based classification
│   ├── ai_classifier.py       # 🤖 NEW: AI classification
│   ├── handler.py             # Lambda handler
│   ├── test_ai_classifier.py  # 🤖 Test AI locally
│   └── requirements.txt       # Python dependencies
├── desktop-app/               # 🖥️ PyQt6 Desktop Application
│   ├── main_gui.py           # Main application window
│   ├── database.py           # Local SQLite manager
│   ├── api_client.py         # AWS API client
│   ├── telegram_notifier.py  # Telegram integration
│   └── modules/              # Feature modules
│       ├── dashboard.py      # Overview & net worth
│       ├── transactions.py   # Transaction list
│       ├── csv_import.py     # CSV import wizard
│       ├── accounts.py       # Account management
│       ├── goals.py          # Goal setting
│       ├── insights.py       # Financial insights
│       └── widgets.py        # Reusable UI components
├── sam-backend/               # AWS SAM deployment
│   ├── template.yaml         # CloudFormation template
│   ├── samconfig.toml        # SAM configuration
│   └── handlers/             # CloudWatch scheduled handlers
├── AI_SETUP.md               # 🤖 AI integration guide
└── README.md                 # This file
```

## 🎯 Usage Guide

### 1. Set Up Your Accounts

**Desktop App**:
1. Go to **🏦 Accounts** tab
2. Enter current balances for each account:
   - 💰 Savings Account
   - 💳 Bills Account
   - 🏦 Main Account
   - 💳 Credit Card (amount you owe)
3. Click **Save** for each

### 2. Import Transactions

**Desktop App**:
1. Go to **📁 CSV Import** tab
2. Select account from dropdown
3. Choose your bank CSV file
4. Review auto-classifications
5. Click **Commit to AWS**

**Supported Formats**:
- ANZ Bank statements
- ASB Bank statements
- BNZ Bank statements
- Generic CSV (date, amount, description)

### 3. View Insights

**Desktop App**:
1. Go to **💰 Insights** tab
2. See:
   - 📊 Financial Health Score
   - 🚨 Spending Alerts
   - 💡 Savings Suggestions
   - 📈 Trends (excludes transfers!)

You can also test the endpoint directly:
```bash
curl "$AWS_API_URL/insights?user_id=user1" | jq
```

### 4. Set Goals

**Desktop App**:
1. Go to **🎯 Goals** tab
2. Click **Add New Goal**
3. Enter:
   - Goal name (e.g., "Vacation Fund")
   - Target amount
   - Current progress
4. Track progress automatically!

### 5. Check Dashboard

**Desktop App**:
1. Go to **📊 Dashboard** tab
2. View:
   - 💰 Net Worth (assets - liabilities)
   - 📈 Total Assets
   - 📉 Total Liabilities
   - 📋 Recent Transactions

## 🔧 Configuration

### Environment Variables

Create `.env` in project root:

```env
# Telegram Notifications (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# AI Classification (optional)
GEMINI_API_KEY=your_gemini_api_key

# Desktop App Local Database (automatically created in desktop-app/finance_tracker.db)
```

### Desktop App Settings

Preferred: set the API URL via `.env` (`AWS_API_URL`). The app reads it automatically on startup—no code edits needed.

## 🧪 Testing

### Test AI Classification
```bash
cd backend
export GEMINI_API_KEY="your_key"
python test_ai_classifier.py
```

### Test Desktop App Locally
```bash
cd desktop-app
python main_gui.py
```

### Test API Endpoints
```bash
# Local
curl http://localhost:8000/categories

# AWS
curl https://your-api-url/ai/status
```

## 🔒 Security & Privacy

### What Data is Shared?

**With Google Gemini AI** (only if enabled):
- ✅ Transaction description (e.g., "MYSTERY CAFE")
- ✅ Transaction amount (e.g., -25.50)
- ❌ NO account numbers
- ❌ NO personal information
- ❌ NO full transaction history

**Google's Privacy Policy**:
- Data NOT used to train models
- Data NOT stored long-term
- Data NOT shared with other users

### Security Features

- API keys in environment variables (never committed)
- Local SQLite database (encrypted at rest on macOS)
- AWS IAM roles with least privilege
- CORS configured for secure API access
- Sensitive files in `.gitignore`

## 📝 CSV Import Format

### Bank Statement Format (Auto-detected)
```csv
Other Party,Amount,Transaction Date
WOOLWORTHS AUCKLAND,-45.67,2024-01-15
SALARY DEPOSIT,5000.00,2024-01-16
UBER TRIP,-32.50,2024-01-17
```

### Generic Format
```csv
date,amount,description,category
2024-01-15,-25.50,Coffee shop,Dining Out
2024-01-16,1200.00,Salary,Income
```

## 🚨 Troubleshooting

### AI Not Working?

1. **Check API key**: `echo $GEMINI_API_KEY`
2. **Check library**: `pip list | grep google-generativeai`
3. **Test directly**: `python test_ai_classifier.py`
4. **Check status**: `curl https://your-api-url/ai/status`

### Desktop App Issues?

1. **Install PyQt6**: `pip install PyQt6`
2. **Check Python version**: `python --version` (needs 3.11+)
3. **Check database**: Look for `finance_tracker.db` in desktop-app/

### AWS Deployment Issues?

```bash
# Check stack status
aws cloudformation describe-stacks --stack-name finance-tracker

# View Lambda logs
cd sam-backend
sam logs -n FinanceTrackerFunction --tail

# Test API
curl -v https://your-api-url/categories
```

## 🎨 Features in Detail

### Transfer Detection

Transactions marked as "payment received" or transfers between your accounts are automatically:
- ✅ Categorized as "Transfers"
- ✅ Excluded from spending insights
- ✅ Excluded from income calculations
- ✅ Not counted in financial health score

This ensures accurate spending analysis!

### Net Worth Calculation

**Formula**: `Assets - Liabilities`

**Assets** (positive):
- Savings Account balance
- Bills Account balance
- Main Account balance

**Liabilities** (negative):
- Credit Card balance (debt)

### Financial Health Score

Calculated from:
- **40%**: Savings rate
- **30%**: Income vs. expenses
- **30%**: Transaction tracking consistency

Score: 0-100 (higher is better!)

## 📚 Additional Resources

- [AI Setup Guide](AI_SETUP.md) - Complete AI integration documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/) - API framework
- [PyQt6 Docs](https://www.riverbankcomputing.com/static/Docs/PyQt6/) - Desktop UI
- [AWS SAM Docs](https://docs.aws.amazon.com/serverless-application-model/) - Deployment
- [Google Gemini API](https://ai.google.dev/) - AI classification

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!

## 📄 License

This project is for personal use. Feel free to adapt for your own finance tracking needs.

---

**Built with ❤️ using FastAPI, AWS Lambda, DynamoDB, PyQt6, and Google Gemini AI**

**Features**: AI Classification 🤖 | Multi-Account Tracking 🏦 | Net Worth Analysis 💰 | Goal Setting 🎯 | Telegram Notifications 📱 | Dark Mode 🌙

# 🏗️ Finance Tracker 2.0

A comprehensive personal finance management system with enhanced features, AWS cloud deployment, and a modern web interface.

## ✨ Features

### Phase 1 - Core Functionality ✅
- **Transaction Management**: Add, view, and track income/expenses
- **Categories & Tags**: Organized categorization with colors and icons
- **Recurring Transactions**: Support for automated recurring bills
- **Enhanced Schema**: Transaction types, frequencies, and metadata
- **Dual Environment**: Works locally (SQLite) and on AWS (DynamoDB)

### Phase 2 - Data Input Automation ✅
- **CSV Import**: Upload bank statements and transaction files
- **Web Interface**: Modern, responsive UI for easy management
- **Real-time Dashboard**: Weekly income/expense summaries
- **Category Management**: Visual category browser with icons

### Future Phases (Planned)
- **Email Receipt Processing**: Automatic transaction extraction from emails
- **Recurring Transaction Automation**: CloudWatch scheduled processing
- **Analytics & Insights**: Spending trends and budget alerts
- **AI Features**: Smart categorization and spending predictions

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- AWS CLI configured
- SAM CLI installed

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <your-repo>
   cd finance-tracker
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

2. **Run locally**:
   ```bash
   cd backend
   python -m uvicorn app:app --reload
   ```

3. **Access the API**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

### Web Interface

1. **Setup frontend**:
   ```bash
   cd frontend
   cp config.js.template config.js
   # Edit config.js with your API URL
   ```

2. **Serve the interface**:
   ```bash
   # Option 1: Python server
   python3 -m http.server 8000
   
   # Option 2: Node.js server
   npx serve .
   
   # Option 3: Open directly
   open index.html
   ```

3. **Access the web interface**: http://localhost:8000

## ☁️ AWS Deployment

### Deploy to AWS

1. **Build and deploy**:
   ```bash
   cd sam-backend
   sam build
   sam deploy --guided
   ```

2. **Configure frontend**:
   ```bash
   cd frontend
   # Update config.js with your deployed API URL
   ```

### AWS Resources Created
- **Lambda Function**: FastAPI application
- **DynamoDB Tables**: Transactions, Categories, Recurring
- **API Gateway**: RESTful API endpoints
- **CloudWatch**: Logging and monitoring

## 📊 API Endpoints

### Transactions
- `POST /transactions` - Add new transaction
- `GET /transactions` - List transactions
- `GET /report` - Get financial summary

### Categories
- `GET /categories` - List all categories

### CSV Import
- `POST /import/csv` - Import transactions from CSV
- `GET /import/template` - Get CSV template

### Recurring Transactions
- `POST /recurring-transactions` - Add recurring transaction
- `GET /recurring-transactions` - List recurring transactions

## 🗂️ Project Structure
inance-tracker/
├── backend/ # FastAPI application
│ ├── app.py # Main application
│ ├── aws_db.py # DynamoDB integration
│ ├── db.py # SQLite integration
│ ├── handler.py # Lambda handler
│ └── requirements.txt # Python dependencies
├── frontend/ # Web interface
│ ├── index.html # Main HTML file
│ ├── css/style.css # Styling
│ ├── js/app.js # JavaScript functionality
│ └── config.js # API configuration (gitignored)
├── sam-backend/ # AWS deployment
│ ├── template.yaml # SAM template
│ ├── samconfig.toml # SAM configuration
│ └── handlers/ # Legacy Lambda handlers
└── README.md # This file

## 🔧 Configuration

### Environment Variables

#### Local Development
Create `.env` file in `backend/`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

#### AWS Deployment
Environment variables are automatically set by SAM:
- `TRANSACTIONS_TABLE`: DynamoDB table name
- `CATEGORIES_TABLE`: Categories table name
- `RECURRING_TABLE`: Recurring transactions table

### Frontend Configuration
Update `frontend/config.js`:
```javascript
const CONFIG = {
    API_BASE_URL: 'https://your-api-gateway-url.amazonaws.com/Prod'
};
```

## 📈 Usage Examples

### Add a Transaction
```bash
curl -X POST https://your-api-url/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "amount": -25.50,
    "category": "Food & Dining",
    "description": "Coffee",
    "type": "expense",
    "tags": "coffee, work"
  }'
```

### Import CSV
```bash
curl -X POST https://your-api-url/import/csv?user_id=user123 \
  -F "file=@transactions.csv"
```

### Get Weekly Report
```bash
curl https://your-api-url/report?user_id=user123&days=7
```

## 🛠️ Development

### Adding New Features

1. **Backend**: Add endpoints in `backend/app.py`
2. **Database**: Update schema in `backend/aws_db.py` and `backend/db.py`
3. **Frontend**: Add UI components in `frontend/`
4. **Deploy**: Update SAM template and redeploy

### Testing

```bash
# Test locally
cd backend
python -m uvicorn app:app --reload

# Test API endpoints
curl http://localhost:8000/categories

# Test web interface
cd frontend
python3 -m http.server 8000
```

## 🔒 Security

- **API Keys**: Stored in environment variables
- **CORS**: Configured for web interface access
- **DynamoDB**: IAM roles with least privilege
- **Git**: Sensitive files in `.gitignore`

## 📝 CSV Format

Expected CSV format for imports:
```csv
date,amount,description,category,tags
2024-01-15,-25.50,Coffee shop,Food & Dining,coffee work
2024-01-16,1200.00,Salary,Salary,income
2024-01-17,-89.99,Groceries,Food & Dining,groceries
```

## 🚨 Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure CORS middleware is configured
2. **DynamoDB Errors**: Check table names and permissions
3. **Import Errors**: Verify CSV format and file encoding
4. **Deployment Issues**: Check SAM build and CloudFormation logs

### Debug Commands

```bash
# Check deployment status
aws cloudformation describe-stacks --stack-name finance-tracker

# View Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/finance"

# Test API directly
curl -v https://your-api-url/categories
```

## 📄 License

This project is for personal use. Feel free to adapt for your own finance tracking needs.

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!

---

**Built with ❤️ using FastAPI, AWS Lambda, DynamoDB, and vanilla JavaScript**
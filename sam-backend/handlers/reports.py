import os, json
import boto3
from datetime import datetime, timedelta
import requests


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TRANSACTIONS_TABLE"])
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SES_FROM = os.environ.get("SES_FROM")
REPORT_TO = os.environ.get("REPORT_TO")


def send_telegram(text):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text})


def lambda_handler(event, context):
    now = datetime.utcnow()
    cuttoff = int((now - timedelta(days=7)).timestamp())
    resp = table.scan()
    items = [i for i in resp.get("Items", []) if int(i["date_ts"]) >= cuttoff]
    income = sum(float(i["amount"]) for i in items if float(i["amount"]) > 0)
    expense = sum(float(i["amount"]) for i in items if float(i["items"]) < 0)
    text = f"Weekly: inome={income:.2f}, expense={expense:.2f}, net={(income + expense):.2f}"
    send_telegram(text)

    if SES_FROM and REPORT_TO:
        ses = boto3.client("ses")
        ses.send_email(
            Source=SES_FROM,
            Destination={"ToAddresses": [REPORT_TO]},
            Message={
                "Subject": {"Data": "Weekly Report"},
                "Body": {"Text": {"Data": text}},
            },
        )
    return {"statusCode": 200, "body": text}

from flask import Flask, request, abort, jsonify
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import mysql.connector
import re
from datetime import datetime
from textwrap import dedent
import subprocess
import sys
import time
import os

app = Flask(__name__)

# ===== CONFIGURATION =====
LINE_CHANNEL_SECRET = "c7170bf37496fe59e045e65cc928b824"
LINE_CHANNEL_ACCESS_TOKEN = "fmFL1YGzs3ZELp+Os0VYmD027BZ7VZNPijimDWDtmVDfCul12HhhHAqljSrDP9veXIHj0RvIXEBPxFx5hkJg0g2H7UljTBBuQtcLCwy3DILm7DnWJ+gcLQ7ZAN/wfJDg10zNKyjfj50/fCcZj+RatQdB04t89/1O/w1cDnyilFU="
handler = WebhookHandler(LINE_CHANNEL_SECRET)
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)

# API key for securing the endpoint
API_KEY = "your-secure-api-key-here"  # Replace with a strong, unique key

DB_CONFIG = {
    "host": "10.1.0.47",
    "user": "root",
    "password": "pTT!CT01",
    "database": "testing_db"
}

def get_sales_data(date):
    """Retrieve sales data with proper error handling and logging"""
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        query = """
                SELECT
                    STATION_ID,
                    STATION,
                    SUM(total_amount) as total_amount,
                    SUM(total_valume) as total_volume
                FROM summary_station_2025_materialized
                WHERE date_completed = %s
                  AND STATION_ID REGEXP '^F[0-9]+$'
                GROUP BY STATION_ID, STATION
                ORDER BY total_amount DESC
                """
        cursor.execute(query, (date,))
        data = cursor.fetchall()
        print(f"DEBUG: Retrieved {len(data)} stations for date {date}")
        return data
    except Exception as e:
        print(f"⚠️ Database Error: {str(e)}")
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

from datetime import datetime

def create_ultimate_report(date, data):
    """Generate a mobile-optimized sales report with perfect readability"""
    if not data:
        return f"📭 No sales data for {date}"

    # Calculate totals and averages
    total_amount = sum(row['total_amount'] for row in data)
    total_volume = sum(row['total_volume'] for row in data)
    avg_amount = total_amount / len(data)
    avg_volume = total_volume / len(data)

    # Find highest and lowest sales
    top = max(data, key=lambda x: x['total_volume'])
    bottom = min(data, key=lambda x: x['total_volume'])

    # Header with branding and date
    report = [
        "⛽ PTT Oil-Retail Sales Performance",
        f"📅 {datetime.strptime(date, '%Y-%m-%d').strftime('%a, %b %d %Y')}",
        "──────────────────",
        "📋 Total Sales Performance",
        f"Total Station: {len(data)}",
        f"Toltal Volume: {total_volume:,.2f} L",
        f"Total Amount: {total_amount:,.2f} USD",
        f"AVG Val/Station: {avg_volume:,.2f} L",
        f"AVG Amt/Station: {avg_amount:,.2f} USD",
        "──────────────────",
        "🏆 Highest Sale Station",
        f"{top['STATION_ID']}: {top['STATION']}",
        f"Volume: {top['total_volume']:,.2f} L",
        f"Amount: {top['total_amount']:,.2f} USD",
        "──────────────────",
        "📉 Lowest Sales Station",
        f"{bottom['STATION_ID']}: {bottom['STATION']}",
        f"Volume: {bottom['total_volume']:,.2f} L",
        f"Amount: {bottom['total_amount']:,.2f} USD",
        "──────────────────"
    ]

    # Performance breakdown with volume and amount shares
    report.append("📊 Station Rankings")
    for idx, row in enumerate(sorted(data, key=lambda x: x['total_volume'], reverse=True), 1):
        volume_share = (row['total_volume'] / total_volume) * 100 if total_volume else 0
        amount_share = (row['total_amount'] / total_amount) * 100 if total_amount else 0
        report.extend([
            f"#{idx} {row['STATION_ID']}",
            f"  {row['STATION']}",
            f"  Vol: {row['total_volume']:,.2f} L",
            f"  Amt: {row['total_amount']:,.2f} USD",
            f"  Vol%: {volume_share:.1f}%",
            f"  Amt%: {amount_share:.1f}%",
            "──────────────────"
        ])

    # Footer with timestamp
    report.extend([
        "📅 Generated on",
        f"  {datetime.now().strftime('%a, %b %d %Y %I:%M %p')}",
        "Powered by Retail System "
    ])

    return "\n".join(report)
@app.route("/callback", methods=["POST"])
def callback():
    """Handle LINE webhook"""
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """Process incoming messages"""
    text = event.message.text.strip()

    # Validate date format
    if not re.match(r"^\d{4}-\d{1,2}-\d{1,2}$", text):
        reply = dedent("""
            📅 Invalid date format
            Please use: YYYY-MM-DD
            Example: 2025-05-15
        """).strip()
        return send_reply(event.reply_token, reply)

    try:
        datetime.strptime(text, "%Y-%m-%d")
        data = get_sales_data(text)
        reply = create_ultimate_report(text, data) if data else f"📭 No data found for {text}"
    except ValueError:
        reply = "⚠️ Invalid date\nUse YYYY-MM-DD format"
    except Exception as e:
        print(f"⛔ Error: {str(e)}")
        reply = "⚠️ Service unavailable\nPlease try later"

    send_reply(event.reply_token, reply)

@app.route('/get_sales_data', methods=['GET'])
def get_sales_data_endpoint():
    """Endpoint to fetch sales data for Google Apps Script with API key authentication"""
    api_key = request.headers.get('Authorization')
    if not api_key or api_key != f"Bearer {API_KEY}":
        print(f"Unauthorized access attempt: {request.remote_addr}")
        return jsonify({"error": "Unauthorized"}), 401

    date = request.args.get('date')
    if not date or not re.match(r"^\d{4}-\d{1,2}-\d{1,2}$", date):
        print(f"Invalid date format from {request.remote_addr}: {date}")
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    data = get_sales_data(date)
    if data:
        print(f"Successfully served data for date {date} to {request.remote_addr}")
        return jsonify(data)
    print(f"No data found for date {date} for {request.remote_addr}")
    return jsonify({"error": "No data found"}), 404

def send_reply(reply_token, message):
    """Send formatted reply"""
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=message)]
            )
        )

def update_line_webhook(webhook_url):
    """Update the LINE webhook URL using the Messaging API"""
    try:
        with ApiClient(configuration) as api_client:
            line_api = MessagingApi(api_client)
            # Update the webhook URL
            line_api.set_webhook_endpoint({
                "endpoint": f"{webhook_url}/callback"
            })
        print(f"Successfully updated LINE webhook to: {webhook_url}/callback")
    except Exception as e:
        print(f"⚠️ Error updating LINE webhook: {str(e)}")

def start_localtunnel():
    """Start Localtunnel to expose the Flask app via HTTPS with a custom subdomain"""
    try:
        # Use shell=True to handle the command correctly on Linux
        process = subprocess.Popen(
            "lt --port 5000 --subdomain my-ptt-station",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Wait to capture the Localtunnel URL
        time.sleep(3)
        url = None
        # Read the output to find the Localtunnel URL with a timeout
        for line in iter(process.stdout.readline, ''):
            if "your url is:" in line.lower():
                url = line.split("your url is:")[1].strip()
                print(f"Localtunnel URL: {url}")
                break
        if not url:
            print("⚠️ Warning: Could not capture Localtunnel URL automatically. Check terminal output manually.")
            return process
        # Update the LINE webhook with the new URL
        update_line_webhook(url)
        return process
    except FileNotFoundError:
        print("⚠️ Error: Localtunnel (lt) not found. Please install it using 'sudo npm install -g localtunnel'.")
        sys.exit(1)
    except Exception as e:
        print(f"⚠️ Error starting Localtunnel: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Start Localtunnel before running the Flask app
    lt_process = start_localtunnel()
    try:
        # Start the Flask app
        app.run(host="0.0.0.0", port=5000)
    finally:
        # Ensure Localtunnel process is terminated when Flask app stops
        lt_process.terminate()
        lt_process.wait()


from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.get_json()
    # Process the webhook data and trigger the trading agent
    # ...
    return 'Webhook received', 200
import os
import json
import base64
import logging
from flask import Flask, request, jsonify

# Import fungsi dari cloud function yang ada
try:
    from cloud_function.main import process_email
except ImportError:
    # Fallback jika import gagal
    def process_email(message):
        return {"status": "error", "message": "Cloud function module not available"}

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_message(message):
    """Validasi format pesan Pub/Sub"""
    if not message:
        return False
    if not isinstance(message, dict):
        return False
    return "data" in message

@app.route("/", methods=["GET"])
def health_check():
    """Endpoint health check"""
    return jsonify({
        "status": "healthy", 
        "service": "auto-reply-email",
        "version": "1.0.0"
    })

@app.route("/process", methods=["POST"])
def handle_request():
    """Endpoint untuk menerima dan memproses pesan Pub/Sub"""
    try:
        envelope = request.get_json()
        if not envelope:
            msg = "No Pub/Sub message received"
            logger.error(msg)
            return jsonify({"error": msg}), 400

        if not isinstance(envelope, dict) or "message" not in envelope:
            msg = "Invalid Pub/Sub message format"
            logger.error(f"{msg}: {envelope}")
            return jsonify({"error": msg}), 400

        # Process the Pub/Sub message
        pubsub_message = envelope["message"]
        
        if not validate_message(pubsub_message):
            msg = "Invalid message format"
            logger.error(f"{msg}: {pubsub_message}")
            return jsonify({"error": msg}), 400

        # Decode message data if base64 encoded
        if "data" in pubsub_message:
            try:
                data = base64.b64decode(pubsub_message["data"]).decode("utf-8")
                pubsub_message["data"] = data
            except Exception as e:
                logger.warning(f"Could not decode message data: {e}")

        # Process the email
        logger.info(f"Processing message: {pubsub_message}")
        
        # Extract recipient from the message if available
        recipient = None
        try:
            if isinstance(pubsub_message.get("data"), str):
                data = json.loads(pubsub_message["data"])
                recipient = data.get("to")
                
                # Check if the email is intended for our specific address
                from config import get_config
                DESTINATION_EMAIL = os.environ.get("DESTINATION_EMAIL", "addhe.warman+cs@gmail.com")
                
                if recipient and recipient != DESTINATION_EMAIL:
                    logger.warning(f"Ignoring email to {recipient} (expected {DESTINATION_EMAIL})")
                    return jsonify({"success": False, "message": "Email not intended for this service"}), 200
        except Exception as e:
            logger.warning(f"Could not extract recipient from message: {e}")
            
        result = process_email(pubsub_message)
        logger.info(f"Processing result: {result}")
        
        
        return jsonify({
            "success": True, 
            "result": result,
            "message": "Email processed successfully"
        })

    except Exception as e:
        logger.exception(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 8080))
    # Use debug=False in production
    app.run(host="0.0.0.0", port=PORT, debug=False)

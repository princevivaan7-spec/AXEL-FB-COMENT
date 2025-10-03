from flask import Flask, request
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
def post_comment(post_id, comment, token):
    url = f"https://graph.facebook.com/{post_id}/comments"
    payload = {"message": comment, "access_token": token}
    response = requests.post(url, data=payload)

    print("FB API Response:", response.text)

    try:
        data = response.json()
        if "id" in data:
            logging.info(f"✅ Comment sent successfully: {data['id']}")
            return True
        else:
            logging.error(f"❌ Failed to send comment: {data}")
            return False
    except Exception as e:
        logging.error(f"⚠️ Error parsing FB response: {e}")
        return False

@app.route("/")
def home():
    return "✅ FB Auto Comment Bot Running!"


@app.route("/comment", methods=["POST"])
def comment():
    try:
        post_id = request.json.get("post_id")
        comment_text = request.json.get("comment")
        token = request.json.get("token")

        if not post_id or not comment_text or not token:
            return {"error": "Missing post_id, comment or token"}, 400

        success = post_comment(post_id, comment_text, token)

        if success:
            return {"status": "Comment posted successfully ✅"}
        else:
            return {"status": "Failed to post comment ❌"}, 500

    except Exception as e:
        logging.error(f"🔥 Exception in /comment route: {e}")
        return {"error": str(e)}, 500


if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=10000)

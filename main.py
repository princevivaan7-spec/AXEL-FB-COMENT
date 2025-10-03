import os
import threading
import time
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

tasks = {}
def send_comments(task_id, post_id, tokens, comments, delay):
    i = 0
    tasks[task_id]["running"] = True
    while tasks[task_id]["running"]:
        token = tokens[i % len(tokens)]
        comment = comments[i % len(comments)]

        url = f"https://graph.facebook.com/{post_id}/comments"
        params = {"message": comment, "access_token": token}
        try:
            res = requests.post(url, data=params)
            print("Response:", res.text)
        except Exception as e:
            print("Error:", e)

        i += 1
        time.sleep(delay)
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    post_id = request.form.get("post_id")
    delay = request.form.get("delay")

    if not delay:
        return jsonify({"error": "Delay is required"}), 400

    try:
        delay = int(delay)
    except ValueError:
        return jsonify({"error": "Delay must be a number"}), 400

    # Token handling
    tokens = []
    if "tokenFile" in request.files and request.files["tokenFile"].filename:
        file = request.files["tokenFile"]
        tokens = file.read().decode("utf-8").splitlines()
    elif request.form.get("singleToken"):
        tokens = [request.form.get("singleToken")]

    if not tokens:
        return jsonify({"error": "No token provided"}), 400

    # Comments file
    if "commentFile" not in request.files or not request.files["commentFile"].filename:
        return jsonify({"error": "No comment file uploaded"}), 400

    comment_file = request.files["commentFile"]
    comments = comment_file.read().decode("utf-8").splitlines()

    task_id = os.urandom(4).hex()
    tasks[task_id] = {"running": True}

    thread = threading.Thread(
        target=send_comments, args=(task_id, post_id, tokens, comments, delay)
    )
    thread.start()

    return jsonify({"status": "Comment task started successfully", "task_id": task_id})


@app.route("/stop", methods=["POST"])
def stop():
    task_id = request.form.get("task_id")
    if task_id in tasks:
        tasks[task_id]["running"] = False
        return jsonify({"status": f"Task {task_id} stopped successfully"})
    return jsonify({"error": "Invalid task_id"}), 400


@app.route("/status")
def status():
    logs = []
    for task_id, task in tasks.items():
        logs.append(f"Task {task_id}: {'Running' if task['running'] else 'Stopped'}")
    return jsonify({"logs": logs})
if __name__ == "__main__":
    from waitress import serve
    port = int(os.environ.get("PORT", 5000))
    serve(app, host="0.0.0.0", port=port)

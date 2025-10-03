import threading
import time
import json
from flask import Flask, request, jsonify

app = Flask(__name__)
tasks = {}

def send_comments(config):
    post_id = config["post_id"]
    token = config["token"]
    comments = config["comments"]
    delay = int(config.get("delay", 5))

    while config["running"]:
        for comment in comments:
            if not config["running"]:
                break
            print(f"Posting comment on {post_id}: {comment} with token {token}")
            # yaha actual FB API call karna hai (currently sirf print ho raha hai)
            time.sleep(delay)

@app.route("/start", methods=["POST"])
def start():
    config = request.json
    task_id = str(len(tasks) + 1)
    config["running"] = True
    tasks[task_id] = config
    t = threading.Thread(target=send_comments, args=(config,))
    t.start()
    return jsonify({"status": "started", "task_id": task_id})

@app.route("/stop", methods=["POST"])
def stop():
    task_id = request.json.get("task_id")
    if task_id in tasks:
        tasks[task_id]["running"] = False
        return jsonify({"status": "stopped", "task_id": task_id})
    return jsonify({"error": "Task not found"}), 404

@app.route("/status")
def status():
    logs = []
    for task_id, task in tasks.items():
        logs.append(f"Task {task_id}: {'Running' if task['running'] else 'Stopped'}")
    return jsonify({"logs": logs})

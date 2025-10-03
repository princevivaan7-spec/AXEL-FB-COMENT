from flask import Flask, render_template, request, jsonify
import threading, time, requests, os, uuid

app = Flask(__name__)

tasks = {}  # {task_id: {"thread": thread, "running": True/False}}

def send_comments(task_id, config):
    tokens = config["tokens"]
    post_id = config["post_id"]
    delay = int(config["delay"])
    cm_file = config["cm_file"]

    if not os.path.exists(cm_file):
        print(f"[x] Comment file not found: {cm_file}")
        return

    with open(cm_file, "r", encoding="utf-8") as f:
        comments = [m.strip() for m in f.readlines() if m.strip()]

    count = 0
    while tasks[task_id]["running"]:
        for i, comment in enumerate(comments):
            if not tasks[task_id]["running"]:
                break
            token = tokens[i % len(tokens)]
            url = f"https://graph.facebook.com/{post_id}/comments"
            payload = {"access_token": token, "message": comment}
            r = requests.post(url, data=payload)
            count += 1
            print(f"[Task {task_id}] Sent {count}: {comment} | Status: {r.status_code}")
            time.sleep(delay)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start_task():
    # Token select
    token_option = request.form.get("tokenOption")
    tokens = []
    if token_option == "single":
        single_token = request.form.get("singleToken")
        if single_token:
            tokens = [single_token.strip()]
    else:
        token_file = request.files.get("tokenFile")
        if token_file:
            content = token_file.read().decode("utf-8")
            tokens = [t.strip() for t in content.splitlines() if t.strip()]

    post_id = request.form.get("postId")
    delay = request.form.get("time")

    # Save comments file
    txt_file = request.files.get("txtFile")
    cm_path = f"cm_{uuid.uuid4().hex}.txt"
    if txt_file:
        txt_file.save(cm_path)

    config = {
        "tokens": tokens,
        "post_id": post_id,
        "delay": delay,
        "cm_file": cm_path
    }

    task_id = str(uuid.uuid4())[:8]
    tasks[task_id] = {"running": True, "thread": None}

    t = threading.Thread(target=send_comments, args=(task_id, config))
    tasks[task_id]["thread"] = t
    t.start()

    return jsonify({"status": f"Comment task started successfully", "task_id": task_id})


@app.route("/stop", methods=["POST"])
def stop_task():
    task_id = request.form.get("taskId")
    if task_id in tasks and tasks[task_id]["running"]:
        tasks[task_id]["running"] = False
        return jsonify({"status": f"Task {task_id} stopped"})
    return jsonify({"status": f"No active task with ID {task_id}"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    @app.route("/status")
def status():
    logs = []
    for task_id, task in tasks.items():
        logs.append(f"Task {task_id}: {'Running' if task['running'] else 'Stopped'}")
    return jsonify({"logs": logs})
